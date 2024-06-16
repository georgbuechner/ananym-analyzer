import os
import shutil
from datetime import date

DATA_DIR = "data/"
BACKUP_LOCATION = "backups/"

today = date.today() 
date_format = today.strftime("%Y_%b_%d_")

shutil.make_archive(os.path.join(BACKUP_LOCATION, date_format), 'zip', DATA_DIR)
