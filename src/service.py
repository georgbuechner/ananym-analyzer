import json
import os
import shutil
from typing import Dict, List, Tuple
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from extractor.functions import DT, Peaks
from extractor.preprocessing import convert_rows_to_columns, extract_data
from extractor.ibw import VERSION, Selection, peaks, plot
from utils import ensure_dir_exists, stem

ALLOWED_EXTENSIONS = {'ibw'}

class Service: 
    def __init__(self, upload_folder) -> None:
        self.dir_raw = os.path.join(upload_folder, "raw")
        self.dir_sweeps = os.path.join(upload_folder, "sweeps")
        self.dir_analysis = os.path.join(upload_folder, "analysis")
        self.dir_peaks = os.path.join(upload_folder, "peaks.json")
        self.peaks = {}
        self.load_peaks()

    def store_peaks(self): 
        with open(self.dir_peaks, "w") as f: 
            json.dump(self.peaks, f)
        
    def load_peaks(self): 
        try: 
            with open(self.dir_peaks, "r") as f: 
                self.peaks = json.load(f)
        except Exception: 
            self.peaks = {}

    def get_raw(self) -> Dict[str, List[Tuple[str, str]]]: 
        raw_data = {}
        for dirpath, _, filenames in os.walk(self.dir_raw):
            if dirpath == self.dir_raw: 
                continue
            relative_path = os.path.relpath(dirpath, self.dir_raw)
            raw_data[relative_path] = [ 
                (f, stem(f)) for f in filenames 
            ]
        return raw_data 

    def get_sweeps(self) -> Dict[str, List[Tuple[str, str, str]]]: 
        raw_data = {}
        for dirpath, _, filenames in os.walk(self.dir_sweeps):
            if dirpath == self.dir_sweeps: 
                continue
            relative_path = os.path.relpath(dirpath, self.dir_sweeps)
            raw_data[relative_path] = [
                self.split_sweeps_name(f) for f in filenames
            ]
        return raw_data

    def get_analysis(self) -> Dict[str, List[Tuple[str, str, str]]]:  
        raw_data = {}
        for dirpath, dirs, _ in os.walk(self.dir_analysis):
            if dirpath == self.dir_analysis or "_sweeps" in dirpath:
                continue
            relative_path = os.path.relpath(dirpath, self.dir_analysis)
            raw_data[relative_path] = [
                self.split_sweeps_name(f) for f in dirs 
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
            self.split_analysis_name(path_to_analysis, f) for f in os.listdir(path_to_analysis)
        ]

    def upload_raw(
        self, file: FileStorage, date: str, extract: bool
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

    def split_sweeps_name(self, name: str) -> Tuple[str, str, str]: 
        return name, name.split("_")[1], name.split("_")[0]

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
        path = os.path.join(
            self.dir_sweeps, date, f'{filename}.json'
        )
        with open(path, "r") as f: 
            data = json.load(f)
            return len(data)

    def do_analysis(
        self, date: str, filename: str, avrg: bool, start: int, end: int
    ) -> Tuple[str, str]: 
        path = os.path.join(
            self.dir_sweeps, date, f'{filename}.json'
        )
        base_path = os.path.join(
            self.dir_analysis, date, filename, f'{"avrg" if avrg else "inrow"}-{start}-{end}_{filename}'
        )
        with open(path, "r") as f: 
            data = json.load(f)
            time = len(data) * DT
            if start > end or start < 0 or end > len(data): 
                return ("start or end invalid!", "success")
            json_data = plot(f"{base_path}.ibw", data, time, Selection(start, end, avrg))
            print("got json data: ", type(json_data), len(json_data))
            with open(f"{base_path}.json", "w") as f: 
                json.dump(json_data, f)
        return ("Successfully analysed data!", "success")

    def calc_peaks(self, path: str, peaks_info: Peaks) -> Dict[int, Dict]: 
        base_path = path.replace(".svg", ".json")
        data_id = os.path.basename(base_path).replace(".json", ".peaks")
        with open(base_path, "r") as f: 
            data = json.load(f)
            peak_data = peaks(data, peaks_info)
            self.peaks[data_id] = peak_data
            return peak_data


def _allowed_file(filename):
    print(filename, filename.rsplit('.', 1)[1].lower())
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
