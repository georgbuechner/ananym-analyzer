import json
import os

class DManager: 
    def __init__(self, upload_folder) -> None:
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

    def load_data(self): 
        with open(self.dir_peaks, "r") as f: 
            self.peaks = json.load(f)
        with open(self.dir_map_num_sweeps, "r") as f: 
            self.map_num_sweeps= json.load(f)
        with open(self.dir_tags, "r") as f: 
            self.tags = json.load(f)
        with open(self.dir_all_tags, "r") as f: 
            self.all_tags = json.load(f)
    
    def add_num_sweeps(self, path: str, num_sweeps: int) -> int: 
        self.map_num_sweeps[path] = num_sweeps
        self.store_num_sweeps()
        return num_sweeps


