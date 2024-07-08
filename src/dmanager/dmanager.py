import json
import os
import shutil
from typing import Dict, List, Tuple

from dmanager.dmodels import Project
from utils import stem

class DManager: 
    def __init__(self, upload_folder) -> None:
        # Dir to database paths
        self.dir_peaks = os.path.join(upload_folder, "peaks.json")
        self.dir_map_num_sweeps = os.path.join(upload_folder, "num_sweeps.json")
        self.dir_tags = os.path.join(upload_folder, "tags.json")
        self.dir_all_tags = os.path.join(upload_folder, "all_tags.json")
        self.dir_favorites = os.path.join(upload_folder, "favorites.json")
        self.dir_projects = os.path.join(upload_folder, "projects")
        # Database fields
        self.peaks = {}
        self.map_num_sweeps = {}
        self.all_tags = []
        self.tags = {}
        self.favorites = {}
        self.projects = self.load_projects()
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
            print("loaded tags: ", self.all_tags)

    def load_projects(self) -> Dict[str, Project]: 
        projects = {}
        for (root, dirs, _) in os.walk(self.dir_projects):
            for dir_name in dirs:
                full_path = os.path.join(root, dir_name)
                full_name = full_path[len(self.dir_projects)+1:]
                projects[full_name] = Project(full_path)
        return projects

    def load_data(self): 
        with open(self.dir_peaks, "r") as f: 
            self.peaks = json.load(f)
        with open(self.dir_map_num_sweeps, "r") as f: 
            self.map_num_sweeps= json.load(f)
        with open(self.dir_tags, "r") as f: 
            self.tags = json.load(f)
        with open(self.dir_all_tags, "r") as f: 
            self.all_tags = json.load(f)
        with open(self.dir_favorites, "r") as f: 
            self.favorites = json.load(f)
   
    def add_num_sweeps(self, path: str, num_sweeps: int) -> int: 
        self.map_num_sweeps[path] = num_sweeps
        self.store_num_sweeps()
        return num_sweeps

    def add_favorite(self, name: str): 
        self.favorites[name] = True
        with open(self.dir_favorites, "w") as f: 
            json.dump(self.favorites, f)

    def del_favorite(self, name: str):
        del self.favorites[name]
        with open(self.dir_favorites, "w") as f: 
            json.dump(self.favorites, f)

    def add_project(self, name: str) -> Tuple[str, str]: 
        if len(name) == 0: 
            return ("missing project name!", "danger")
        if name in self.projects: 
            return ("Project already exists!", "danger")
        project_path = os.path.join(self.dir_projects, name)
        os.mkdir(project_path)
        self.projects[name] = Project(project_path)
        return (f"Sucessfully added project: {name}", "success")

    def del_project(self, name: str) -> Tuple[str, str]: 
        if name not in self.projects: 
            return ("Project does not exist!", "danger")
        project_path = os.path.join(self.dir_projects, name)
        shutil.rmtree(project_path)
        size_before = len(self.projects)
        self.projects = self.load_projects()
        num_deleted = size_before-len(self.projects)
        if num_deleted > 1:
            return (
                f"Sucessfully removed project: {name} and {num_deleted-1} others",
                "success"
            )
        else:
            return (f"Sucessfully removed project: {name}", "success")

    def get_project_analysis(self, project_name: str) -> List[str]: 
        project_analysis = []
        project_path = os.path.join(self.dir_projects, project_name)
        for filename in os.listdir(project_path):
            f = os.path.join(project_path, filename)
            # checking if it is a file and only base path (not .png AND .svg)
            if os.path.isfile(f) and ".png" in filename:
                project_analysis.append(stem(f))
        return project_analysis
