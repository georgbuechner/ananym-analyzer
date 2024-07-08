import json
import os
from dataclasses import dataclass
from enum import Enum
from typing import Tuple

ANALYSIS_INIT = "project.json"

class AnalysisOpts(Enum):
    ALL = 1
    AVRG = 2
    INROW = 3
    STACKED = 4

@dataclass
class Tag: 
    name: str 
    raw: bool

class Project: 
    def __init__(self, path: str) -> None:
        self.path = path 
        # Load analysis included in project
        self.project_file = os.path.join(self.path, ANALYSIS_INIT)
        if os.path.exists(self.project_file): 
            with open(self.project_file, "r") as f: 
                self.analysis = json.load(f) 
        else: 
            self.analysis = []
            self.safe()

    def add(self, analysis: str) -> Tuple[str, int]: 
        if analysis in self.analysis: 
            return ("Analysis already in project", 401)
        self.analysis.append(analysis) 
        self.safe()
        return ("Added analysis to project", 200)

    def remove(self, analysis: str) -> Tuple[str, int]: 
        if analysis not in self.analysis:
            return ("Analysis not in project", 404)
        self.analysis.remove(analysis) 
        self.safe()
        return ("removed analysis from project", 200)
            

    def safe(self) -> None: 
        with open(self.project_file, "w") as f: 
            json.dump(self.analysis, f)
