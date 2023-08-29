import hashlib
import os
from pathlib import Path
from datetime import datetime
from time import tzname

import pytz

LOCAL_FOLDER = "experiment_folder" # Absolute path to Folder

class LocalWorker:

    def __init__(self, local_folder):
        self.folder = Path(local_folder)
    def query_local_files(self):
        pathes = list(self.folder.glob("*"))

        return {path.name : {"path": path,
                             "modifiedTime":datetime.utcfromtimestamp(os.path.getmtime(path)).astimezone(pytz.utc),
                             "md5Checksum": hashlib.md5(open(path,'rb').read()).hexdigest()}
                for path in pathes}