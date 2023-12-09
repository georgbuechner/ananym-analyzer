import os 

def ensure_dir_exists(path: str) -> None: 
    directory = os.path.dirname(path)
    if not os.path.exists(directory): 
        os.makedirs(directory) 

