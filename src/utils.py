import os
from re import A

def ensure_dir_exists(path: str) -> None: 
    directory = os.path.dirname(path)
    if not os.path.exists(directory): 
        print("Creating dirs: ", path, directory)
        os.makedirs(directory) 

def stem(path: str) -> str:
    """ Gets path without extension (f.e. "path/to/dir" from "path/to/dir.txt")
    """
    return os.path.splitext(path)[0]
