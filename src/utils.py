import os 
from PIL import Image

def ensure_dir_exists(path: str) -> None: 
    directory = os.path.dirname(path)
    if not os.path.exists(directory): 
        print("Creating dirs: ", path, directory)
        os.makedirs(directory) 

# def reduze_file_size(path: str) -> None: 
#     foo = Image.open(path)  # My image is a 200x374 jpeg that is 102kb large
#     foo.size  # (200, 374)
#     # downsize the image with an ANTIALIAS filter (gives the highest quality)
#     # foo = foo.resize((160,300),Image.LANCZOS)
#     foo.save(f"{path}.opt.svg", optimize=True, quality=85)  # The saved downsized image size is 22.9kb

def stem(filename: str) -> str:
    return os.path.splitext(filename)[0]
