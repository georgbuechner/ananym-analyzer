from collections.abc import Callable
import json
import os
import re
import shutil
from typing import Dict, List, OrderedDict, Tuple
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from dmanager.dmanager import DManager
from dmanager.dmodels import AnalysisOpts
from dmanager.models import Analysis, Sweep, Raw
from extractor.functions import Peaks
from extractor.plotting import plot_data
from extractor.preprocessing import convert_rows_to_columns, extract_data, join_lists
from extractor.ibw import VERSION, Selection, peaks, get_range
from utils import ensure_dir_exists, stem

type Data = Dict[str, List[Raw|Sweep]]

ALLOWED_EXTENSIONS = {'ibw'}


class Service: 
    def __init__(self, upload_folder) -> None:
        self.dmanager = DManager(upload_folder)
        self.dir_raw = os.path.join(upload_folder, "raw")
        self.dir_sweeps = os.path.join(upload_folder, "sweeps")
        self.dir_analysis = os.path.join(upload_folder, "analysis")

    def add_tag_to_entry(self, path, tag): 
        # If tag already exists for entry, do nothing
        if path in self.dmanager.tags and tag in self.dmanager.tags[path]:
            return
        # Add tag if not exists
        if tag not in self.dmanager.all_tags: 
            self.dmanager.all_tags.append(tag) 
        # Add tags to entry
        if path in self.dmanager.tags:
            self.dmanager.tags[path].append(tag)
        else: 
            self.dmanager.tags[path] = [tag]
        self.dmanager.store_tags()

    def remove_tag_from_entry(self, path, tag): 
        if path in self.dmanager.tags: 
            if tag in self.dmanager.tags[path]: 
                self.dmanager.tags[path].remove(tag)
      
    def get_raw(self) -> Dict[str, List[Raw]]: 
        raw_data = {}
        for dirpath, _, filenames in os.walk(self.dir_raw):
            if dirpath == self.dir_raw: 
                continue
            relative_path = os.path.relpath(dirpath, self.dir_raw)
            raws = [Raw(self.dmanager, relative_path, f) for f in filenames]
            raws.sort(key=(lambda x: _get_key_num(x.filename)))
            raw_data[relative_path] = raws
        return OrderedDict(sorted(raw_data.items()))

    def get_sweeps(self) -> Dict[str, List[Sweep]]: 
        sweeps_data = {}
        for dirpath, _, filenames in os.walk(self.dir_sweeps):
            if dirpath == self.dir_sweeps: 
                continue
            relative_path = os.path.relpath(dirpath, self.dir_sweeps)
            sweeps = [Sweep(self.dmanager, relative_path, stem(f)) for f in filenames]
            sweeps.sort(key=(lambda x: _get_key_num(x.name)))
            sweeps_data[relative_path] = sweeps
        return OrderedDict(sorted(sweeps_data.items()))

    def get_analysis(self) -> Dict[str, List[Sweep]]:  
        sweeps_data = {}
        for dirpath, dirs, _ in os.walk(self.dir_analysis):
            if dirpath == self.dir_analysis or "_sweeps" in dirpath:
                continue
            relative_path = os.path.relpath(dirpath, self.dir_analysis)
            sweeps = [Sweep(self.dmanager, relative_path, f) for f in dirs]
            sweeps.sort(key=(lambda x: _get_key_num(x.name)))
            sweeps_data[relative_path] = sweeps
        return OrderedDict(sorted(sweeps_data.items()))

    def get_searched(self, get_data_func: Callable[[], Data], tags: str) -> Data: 
        data = get_data_func()
        for tag in [t for t in tags.split(";") if len(t) > 0]: 
            reduced = {} 
            for date, xs in data.items(): 
                reduced[date] = [x for x in xs if x.tags_match(tag)]
            data = reduced
        return {date:xs for date, xs in data.items() if len(xs) > 0}

    def get_single_analysis(
        self, date: str, filename: str, only_favorites: bool
    ) -> List[Analysis]:
        path = os.path.join(self.dir_analysis, date, filename)
        ensure_dir_exists(f"{path}/")
        favorites = self.dmanager.favorites
        analysis_data = [
            Analysis(path, f) for f in os.listdir(path) 
            if ".png" in f and (not only_favorites or os.path.join(path, f) in favorites)
        ]
        # Sort by selection
        def get_selection(elem: Analysis): 
            return elem.selection
        analysis_data.sort(key=get_selection)
        return analysis_data

    def upload_raw(
        self, file: FileStorage, date: str, extract: bool, tags: str
    ) -> Tuple[str, str]:
        if file.filename == '' or date == '':
            return ('No file or creation-date', 'danger')
        if file and _allowed_file(file.filename):
            # Store file if not exists
            filename = secure_filename(file.filename)
            path_to_file = os.path.join(self.dir_raw, date, filename)
            if os.path.exists(path_to_file): 
                return ('File already exists ', 'danger')
            # Store
            ensure_dir_exists(path_to_file)
            file.save(path_to_file)
            for tag in tags.split(", "): 
                self.add_tag_to_entry(os.path.join(date, stem(filename)), tag)
            # If extraxting is desired, extract sweeps
            if extract: 
                _, _ = self.unpack_raw(date, filename)
            return ('Upload success!', 'success')
        else: 
            return ('Invalid file type!', 'danger')
    
    def delete_data(
        self, base_path: str, date: str, filename: str
    ) -> Tuple[str, str]: 
        path_to_file = os.path.join(base_path, date, filename)
        if not os.path.exists(path_to_file): 
            return ('File does not exist! ', 'danger')
        if os.path.isdir(path_to_file): 
            shutil.rmtree(path_to_file)
        else:
            os.remove(path_to_file)
        # If directory is now empty, remove directory too
        directory = os.path.dirname(path_to_file)
        if len(os.listdir(directory)) == 0: 
            shutil.rmtree(directory)
        return ('Data successfully removed.', 'success')

    def unpack_raw(self, date: str, filename: str) -> Tuple[str, str]: 
        path_to_file = os.path.join(self.dir_raw, date, filename)
        data = extract_data(path_to_file, False) 
        sweeps = convert_rows_to_columns(data, len(data[0]))
        path_to_data = os.path.join(
            self.dir_sweeps, date, f'{VERSION}_{stem(filename)}_sweeps.json'
        )
        ensure_dir_exists(path_to_data)
        if os.path.exists(path_to_data):
            return ("Unpacked data already exists!", "danger")
        with open(path_to_data, 'w') as f:
            json.dump(sweeps, f)
        return ("Data successfully unpacked", "success")

    def num_sweeps(self, date:str, filename: str) -> int:  
        print("loading num sweeps:")
        path = os.path.join(
            self.dir_sweeps, date, f'{filename}.json'
        )
        if path in self.dmanager.map_num_sweeps: 
            return self.dmanager.map_num_sweeps[path] 
        with open(path, "r") as f: 
            data = json.load(f)
            return self.dmanager.add_num_sweeps(path, len(data))

    def do_analysis(
        self, 
        date: str, 
        filename: str, 
        opt: AnalysisOpts,
        start: int,
        end: int, 
        ylim: Tuple[float, float], 
    ) -> Tuple[str, str]: 
        path = os.path.join(
            self.dir_sweeps, date, f'{filename}.json'
        )
        base_path = self._create_analysis_path(date, filename, opt, start, end)
        print("GOT base_path:", base_path)
        # Load sweeps
        with open(path, "r") as f: 
            all_sweeps = json.load(f)
        # Get sweeps in specified range 
        if start > end or start < 0 or end > len(all_sweeps): 
            return ("start or end invalid!", "success")
        sweeps, time = get_range(
            all_sweeps, Selection(start, end, opt==AnalysisOpts.AVRG)
        )
        if opt == AnalysisOpts.AVRG or opt == AnalysisOpts.INROW:
            print("Doing AVRG/INROW:")
            plot_data(
                f"{base_path}.ibw", join_lists(sweeps), len(sweeps)*time, ylim=ylim
            )
            # Store sweep-selection
            with open(f"{base_path}.json", "w") as f: 
                json.dump(sweeps, f)
        elif opt == AnalysisOpts.ALL: 
            print("Doing ALL")
            for index, sweep in enumerate(sweeps):
                sweep_path = base_path.replace("XX", str(index).zfill(2))
                plot_data(f"{sweep_path}.ibw", sweep, time, ylim=ylim)
                # Store sweep-selection
                with open(f"{sweep_path}.json", "w") as f: 
                    json.dump([sweep], f)
        elif opt == AnalysisOpts.STACKED: 
            plot_data(f"{base_path}.ibw", sweeps, time, ylim=ylim)
        return ("Successfully analysed data!", "success")

    def calc_peaks(self, path: str, peaks_info: Peaks) -> Dict[int, Dict]: 
        base_path = path.replace(".svg" if "svg" in path else ".png", ".json")
        with open(base_path, "r") as f: 
            sweeps = json.load(f)
            peak_data, time = peaks(sweeps, peaks_info)
            plugin_path = os.path.join(f"{stem(base_path)}_plug", "peaks/")
            ensure_dir_exists(plugin_path)
            reduced = {} 
            for key, value in peak_data.items(): 
                reduced[key] = value["df"]
                sweep_path = os.path.join(plugin_path, key)
                plot_data(
                    f"{sweep_path}.ibw", 
                    sweeps[int(key)], 
                    time,
                    min_peaks=value["min"],
                    max_peaks=value["max"]
                )
            # Save plot and data 
            with open(os.path.join(plugin_path, "data.json"), "w") as f: 
                json.dump(reduced, f)
            return reduced

    def _create_analysis_path(
        self, date: str, filename: str, opt: AnalysisOpts, start: int, end: int
    ) -> str: 
        if opt == AnalysisOpts.ALL: 
            name = f"sweep-XX_{filename}"
        elif opt == AnalysisOpts.AVRG:
            name = f'avrg-{start}-{end}_{filename}'
        elif opt == AnalysisOpts.INROW:
            name = f'inrow-{start}-{end}_{filename}'
        else: 
            name = f'stacked-{start}-{end}_{filename}'
        return os.path.join(self.dir_analysis, date, filename, name)


def _allowed_file(filename):
    print(filename, filename.rsplit('.', 1)[1].lower())
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def _get_key_num(name: str) -> str: 
    try:
        re_str = r"\S(\d\d?)\S*"
        m = re.search(re_str, name) 
        print("Found: ", m.group(1).rjust(3, "0"))
        return m.group(1).rjust(3, "0")
    except Exception as err: 
        print("Failed to get num from {name}: {repr(err)}")
        return name
