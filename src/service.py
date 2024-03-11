import json
import os
import shutil
from typing import Dict, List, Tuple
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from dmanager import DManager
from dmodels import Analysis, Sweep, Raw
from extractor.functions import Peaks
from extractor.plotting import plot_data
from extractor.preprocessing import convert_rows_to_columns, extract_data, join_lists
from extractor.ibw import VERSION, Selection, peaks, get_range
from utils import ensure_dir_exists, stem

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
            raw_data[relative_path] = [ 
                Raw(self.dmanager, relative_path, f) for f in filenames
            ]
        return raw_data 

    def get_sweeps(self) -> Dict[str, List[Sweep]]: 
        raw_data = {}
        for dirpath, _, filenames in os.walk(self.dir_sweeps):
            if dirpath == self.dir_sweeps: 
                continue
            relative_path = os.path.relpath(dirpath, self.dir_sweeps)
            raw_data[relative_path] = [
                Sweep(self.dmanager, relative_path, stem(f)) for f in filenames
            ]
        return raw_data

    def get_analysis(self) -> Dict[str, List[Sweep]]:  
        raw_data = {}
        for dirpath, dirs, _ in os.walk(self.dir_analysis):
            if dirpath == self.dir_analysis or "_sweeps" in dirpath:
                continue
            relative_path = os.path.relpath(dirpath, self.dir_analysis)
            raw_data[relative_path] = [
                Sweep(self.dmanager, relative_path, f) for f in dirs 
            ]
        return raw_data 

    def get_single_analysis(self, date: str, filename: str) -> List[Analysis]:
        path = os.path.join(self.dir_analysis, date, filename)
        ensure_dir_exists(f"{path}/")
        analysis_data = [
            Analysis(path, f) for f in os.listdir(path) if ".png" in f
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
            return self.dmanager(path, len(data))

    def do_analysis(
        self, date: str, filename: str, avrg: bool, use_all: bool, start: int, end: int
    ) -> Tuple[str, str]: 
        if avrg and use_all: 
            return ("Can't use 'avrg' and 'all' at the same time!", "danger")
        path = os.path.join(
            self.dir_sweeps, date, f'{filename}.json'
        )
        base_path = os.path.join(
            self.dir_analysis, date, filename, f'{"avrg" if avrg else "inrow"}-{start}-{end}_{filename}'
        )
        # Load sweeps
        with open(path, "r") as f: 
            sweeps = json.load(f)
            if start > end or start < 0 or end > len(sweeps): 
                return ("start or end invalid!", "success")
            ranged_sweeps, time = get_range(sweeps, Selection(start, end, avrg))
            if not use_all:
                plot_data(f"{base_path}.ibw", join_lists(ranged_sweeps), len(ranged_sweeps)*time)
                # Store sweep-selection
                with open(f"{base_path}.json", "w") as f: 
                    json.dump(ranged_sweeps, f)
            else: 
                for index, sweep in enumerate(ranged_sweeps):
                    base_path = os.path.join(
                        self.dir_analysis, date, filename, f'sweep-{str(index).zfill(2)}_{filename}'
                    )
                    plot_data(f"{base_path}.ibw", sweep, time)
                    # Store sweep-selection
                    with open(f"{base_path}.json", "w") as f: 
                        json.dump([sweep], f)
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


def _allowed_file(filename):
    print(filename, filename.rsplit('.', 1)[1].lower())
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
