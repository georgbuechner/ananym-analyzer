import json
import os
from dataclasses import dataclass
from enum import Enum
from typing import List

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

    def add(self, analysis: str) -> None: 
        self.analysis.append(analysis) 
        self.safe()

    def remove(self, analysis: str) -> None: 
        self.analysis.remove(analysis) 
        self.safe()

    def safe(self) -> None: 
        with open(self.project_file, "w") as f: 
            json.dump(self.analysis, f)


