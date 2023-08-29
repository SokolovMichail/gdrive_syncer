import datetime
from typing import Dict

from src.drive_worker import DriveWorker
from src.local_worker import LocalWorker


class Synchronizer:
    def __init__(self):
        self.drive_worker = DriveWorker()
        self.local_worker = LocalWorker()

    def generate_mod_lists(self, drive_files: Dict, files: Dict):
        drive_set = set(drive_files.keys())
        local_set = set(files.keys())
        upload_list = list(local_set.difference(drive_set))
        download_list = list(drive_set.difference(local_set))
        update_list = []
        for item in local_set.intersection(drive_set):
            hash_difference = drive_files[item]['md5Checksum'] != files[item]['md5Checksum']
            diff_exceeds_one_minute = abs(
                drive_files[item]['modifiedTime'] - files[item]['modifiedTime']) > datetime.timedelta(minutes=1)
            if hash_difference and drive_files[item]['modifiedTime'] > files[item]['modifiedTime'] and diff_exceeds_one_minute:
                download_list.append(item)
            elif hash_difference and drive_files[item]['modifiedTime'] < files[item]['modifiedTime'] and diff_exceeds_one_minute:
                update_list.append(item)
        return upload_list, download_list, update_list

    def query_files(self):
        drive_files = self.drive_worker.query_files_from_folder()
        files = self.local_worker.query_local_files()
        return drive_files, files

    def synchronize(self):
        drive_files, files = self.query_files()
        upload_list, download_list, update_list = self.generate_mod_lists(drive_files, files)
        for item in upload_list:
            self.drive_worker.upload_file(item,drive_files,files)
        for item in download_list:
            self.drive_worker.download_file(item,drive_files,files, self.local_worker.folder)
        for item in update_list:
            self.drive_worker.update_file(item,drive_files,files)
        print("1")
