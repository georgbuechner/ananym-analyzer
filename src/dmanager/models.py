import json
import os
from dmanager.dmanager import DManager
from utils import stem
from typing import List
from dmanager.dmodels import Tag

class Raw: 
    def __init__(self, dmanager: DManager, path: str, filename: str):
        self.path = path 
        self.filename = filename 
        self.name = stem(filename) 
        self.tags = get_tags(dmanager, path, self.name)

    def tags_match(self, tag: str) -> bool: 
        for t in self.tags: 
            if tag in t.name: 
                return True 
        return False

class Sweep: 
    def __init__(self, dmanager: DManager, date: str, filename: str) -> None:
        self.filename = filename
        self.name = filename.split("_")[1]
        self.version = filename.split("_")[0]
        self.tags = get_tags(dmanager, date, self.name, filename)

    def tags_match(self, tag: str) -> bool: 
        for t in self.tags: 
            if tag in t.name: 
                return True 
        return False

class Analysis: 
    def __init__(self, path: str, name: str) -> None:
        self.path = os.path.join(path, name)
        self.selection = name.split("_")[0]
        self.version = name.split("_")[1]
        self.name = name.split("_")[2]
        self.plug = {}
        path_to_plugin_data = os.path.join(path, name.replace(".png", "_plug"))
        if os.path.exists(path_to_plugin_data): 
            for entry in os.scandir(path_to_plugin_data):
                if entry.is_dir():
                    self.plug[entry.name] = PluginData(
                        os.path.join(path_to_plugin_data, entry.name)
                    )

class PluginData: 
    def __init__(self, path: str):
        self.path_to_plot = path
        with open(os.path.join(path, "data.json"), "r") as f: 
            self.data = json.load(f)

def get_tags(
    dmanager: DManager, date: str, filename: str, name: str = ""
) -> List[Tag]:
    tags = []
    raw_id = os.path.join(date, filename)
    analysis_id = os.path.join(raw_id, name)
    for tag_type in [raw_id, analysis_id]:
        if tag_type in dmanager.tags: 
            for tag in dmanager.tags[tag_type]:
                if tag not in tags: 
                    tags.append(Tag(tag, tag_type==raw_id))
    tags.sort(key=(lambda x: x.name))
    return tags
