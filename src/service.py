import json
import os
import shutil
from typing import Dict, List, Tuple
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from extractor.functions import DT
from extractor.preprocessing import convert_rows_to_columns, extract_data
from extractor.ibw import VERSION, average, first_last, in_a_row
from utils import ensure_dir_exists, stem

ALLOWED_EXTENSIONS = {'ibw'}

class Service: 
    def __init__(self, upload_folder) -> None:
        self.dir_raw = os.path.join(upload_folder, "raw")
        self.dir_sweeps = os.path.join(upload_folder, "sweeps")
        self.dir_analysis = os.path.join(upload_folder, "analysis")

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

    def get_analysis(self, date: str, filename: str) -> List[str]: 
        """
        Attributes:
            date: str 
            filename: str (extension alreay removed)
        """
        path_to_analysis = os.path.join(self.dir_analysis, date, filename)
        ensure_dir_exists(f"{path_to_analysis}/")
        return [
            os.path.join(path_to_analysis, f) for f in os.listdir(path_to_analysis)
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
        if not os.path.exists(path_to_file): 
            return ('File does not exist! ', 'danger')
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

    def do_analysis(
        self, date, filename: str, sweep_selection: str
    ) -> Tuple[str, str]: 
        path = os.path.join(
            self.dir_sweeps, date, f'{filename}.json'
        )
        fig_path = os.path.join(
            self.dir_analysis, date, filename, f'{filename}.ibw'
        )
        with open(path, "r") as f: 
            data = json.load(f)
            time = len(data) * DT
            if sweep_selection == "in_a_row": 
                in_a_row(fig_path, data, time)
            elif sweep_selection == "first_last": 
                first_last(fig_path, data, time)
            elif sweep_selection == "average": 
                average(fig_path, data, time, 0.2, 0.1, 0.002)
        return ("Successfully analysed data!", "success")


def _allowed_file(filename):
    print(filename, filename.rsplit('.', 1)[1].lower())
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


