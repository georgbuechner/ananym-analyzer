import json
import os
import shutil
from typing import Dict, List, Tuple
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from extractor.functions import Peaks
from extractor.preprocessing import convert_rows_to_columns, extract_data, join_lists
from extractor.ibw import VERSION, Selection, peaks, plot_data, get_range
from utils import ensure_dir_exists, stem

ALLOWED_EXTENSIONS = {'ibw'}

class Service: 
    def __init__(self, upload_folder) -> None:
        self.dir_raw = os.path.join(upload_folder, "raw")
        self.dir_sweeps = os.path.join(upload_folder, "sweeps")
        self.dir_analysis = os.path.join(upload_folder, "analysis")
        # Dir to database paths
        self.dir_peaks = os.path.join(upload_folder, "peaks.json")
        self.dir_map_num_sweeps = os.path.join(upload_folder, "num_sweeps.json")
        self.dir_tags = os.path.join(upload_folder, "tags.json")
        self.dir_all_tags = os.path.join(upload_folder, "all_tags.json")
        # Database fields
        self.peaks = {}
        self.map_num_sweeps = {}
        self.all_tags = []
        self.tags = {}
        print("loading tags: ", self.all_tags)
        self.load_data()

    def store_peaks(self): 
        with open(self.dir_peaks, "w") as f: 
            json.dump(self.peaks, f)

    def store_num_sweeps(self): 
         with open(self.dir_map_num_sweeps, "w") as f: 
            json.dump(self.map_num_sweeps, f)

    def store_tags(self): 
         with open(self.dir_tags, "w") as f: 
            json.dump(self.tags, f)
         with open(self.dir_all_tags, "w") as f: 
            json.dump(self.all_tags, f)
            print("lOaded tags: ", self.all_tags)

    def add_tag_to_entry(self, path, tag): 
        # If tag already exists for entry, do nothing
        if path in self.tags and tag in self.tags[path]: 
            return
        # Add tag if not exists
        if tag not in self.all_tags: 
            self.all_tags.append(tag) 
        # Add tags to entry
        if path in self.tags:
            self.tags[path].append(tag)
        else: 
            self.tags[path] = [tag]
        self.store_tags()

    def remove_tag_from_entry(self, path, tag): 
        if path in self.tags: 
            if tag in self.tags[path]: 
                self.tags[path].remove(tag)
      
    def load_data(self): 
        with open(self.dir_peaks, "r") as f: 
            self.peaks = json.load(f)
        with open(self.dir_map_num_sweeps, "r") as f: 
            self.map_num_sweeps= json.load(f)
        with open(self.dir_tags, "r") as f: 
            self.tags = json.load(f)
        with open(self.dir_all_tags, "r") as f: 
            self.all_tags = json.load(f)

    def get_raw(self) -> Dict[str, List[Tuple[str, str]]]: 
        raw_data = {}
        for dirpath, _, filenames in os.walk(self.dir_raw):
            if dirpath == self.dir_raw: 
                continue
            relative_path = os.path.relpath(dirpath, self.dir_raw)
            raw_data[relative_path] = [ 
                (f, stem(f), self.__get_tags(relative_path, stem(f))) for f in filenames 
            ]
        return raw_data 

    def get_sweeps(self) -> Dict[str, List[Tuple[str, str, str]]]: 
        raw_data = {}
        for dirpath, _, filenames in os.walk(self.dir_sweeps):
            if dirpath == self.dir_sweeps: 
                continue
            relative_path = os.path.relpath(dirpath, self.dir_sweeps)
            raw_data[relative_path] = [
                self.split_sweeps_name(relative_path, stem(f)) for f in filenames
            ]
        return raw_data

    def get_analysis(self) -> Dict[str, List[Tuple[str, str, str]]]:  
        raw_data = {}
        for dirpath, dirs, _ in os.walk(self.dir_analysis):
            if dirpath == self.dir_analysis or "_sweeps" in dirpath:
                continue
            relative_path = os.path.relpath(dirpath, self.dir_analysis)
            raw_data[relative_path] = [
                self.split_sweeps_name(relative_path, f) for f in dirs 
            ]
        return raw_data 

    def get_single_analysis(
        self, date: str, filename: str
    ) -> List[Tuple[str, str, str, str]]: 
        """
        Attributes:
            date: str 
            filename: str (extension alreay removed)
        """
        path_to_analysis = os.path.join(self.dir_analysis, date, filename)
        ensure_dir_exists(f"{path_to_analysis}/")
        return [
            self.split_analysis_name(path_to_analysis, f) 
            for f in os.listdir(path_to_analysis) 
            if ".png" in f 
        ]

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
        print("Deleting file: ", path_to_file, os.path.exists(path_to_file))
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

    def split_sweeps_name(
        self, date: str, filename: str
    ) -> Tuple[str, str, str, List[str]]: 
        name = filename.split("_")[1]
        version = filename.split("_")[0]
        tags = self.__get_tags(date, name, filename)
        return filename, name, version, tags

    def split_analysis_name(self, path: str, name: str) -> Tuple[str, str, str, str]: 
        """
            returns path+filename, name, sweep_selection, version
        """
        return (
            os.path.join(path, name), 
            name.split("_")[2], 
            name.split("_")[0],
            name.split("_")[1]
        )

    def num_sweeps(self, date:str, filename: str) -> int:  
        print("loading num sweeps:")
        path = os.path.join(
            self.dir_sweeps, date, f'{filename}.json'
        )
        if path in self.map_num_sweeps: 
            return self.map_num_sweeps[path] 
        with open(path, "r") as f: 
            data = json.load(f)
            num_sweeps = len(data)
            self.map_num_sweeps[path] = num_sweeps
            self.store_num_sweeps()
            return num_sweeps

    def do_analysis(
        self, date: str, filename: str, avrg: bool, start: int, end: int
    ) -> Tuple[str, str]: 
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
            print("Got ranged sweeps: ", len(ranged_sweeps), len(ranged_sweeps[0]))
            plot_data(f"{base_path}.ibw", join_lists(ranged_sweeps), time)
            # Store sweep-selection
            with open(f"{base_path}.json", "w") as f: 
                json.dump(ranged_sweeps, f)
        return ("Successfully analysed data!", "success")

    def calc_peaks(self, path: str, peaks_info: Peaks) -> Dict[int, Dict]: 
        base_path = path.replace(".svg", ".json")
        data_id = os.path.basename(base_path).replace(".json", ".peaks")
        with open(base_path, "r") as f: 
            data = json.load(f)
            peak_data = peaks(data, peaks_info)
            self.peaks[data_id] = peak_data
            return peak_data

    def __get_tags(
        self, date: str, filename: str, name: str = ""
    ) -> List[Tuple[str, int]]:
        tags = []
        base_id = os.path.join(date, filename)
        joined_id = os.path.join(base_id, name)
        print("Checking: ", base_id, joined_id)
        for id in [base_id, joined_id]:
            if id in self.tags: 
                for tag in self.tags[id]:
                    if tag not in tags: 
                        tags.append((tag, id==base_id))
        print("found: ", tags)
        return tags


def _allowed_file(filename):
    print(filename, filename.rsplit('.', 1)[1].lower())
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
