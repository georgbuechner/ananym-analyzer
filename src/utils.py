import os 

def ensure_dir_exists(path: str) -> None: 
    directory = os.path.dirname(path)
    if not os.path.exists(directory): 
        print("Creating dirs: ", path, directory)
        os.makedirs(directory) 

def stem(filename: str) -> str:
    return os.path.splitext(filename)[0]
