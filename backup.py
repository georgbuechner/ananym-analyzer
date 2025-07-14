import os
import json
import shutil
from datetime import date

with open("server.config") as f:
    config = json.load(f)
    DATA_DIR = config["upload_folder"]
    BACKUP_LOCATION = config["backups"]

today = date.today() 
date_format = today.strftime("%Y_%b_%d_")

shutil.make_archive(os.path.join(BACKUP_LOCATION, date_format), 'zip', DATA_DIR)
