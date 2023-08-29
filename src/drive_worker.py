import io
import os
from pathlib import Path
from typing import List, Dict
import datetime as dt

import iso8601
import rfc3339
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive',"https://www.googleapis.com/auth/drive.metadata"]
GOOGLE_DRIVE_SYNCHRONIZATION_FOLDER = "KeePassFolder"

def get_date_object(date_string):
  return iso8601.parse_date(date_string)

def get_date_string(date_object):
  return rfc3339.rfc3339(date_object)

class DriveWorker:
    def __init__(self):
        self.creds = DriveWorker.get_credentials()
        self.service = build('drive', 'v3', credentials=self.creds)

    @staticmethod
    def get_credentials():
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json')
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'creds.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        return creds

    def query_folder(self):
        folderId = self.service.files().list(
            q=f"mimeType = 'application/vnd.google-apps.folder' and name = '{GOOGLE_DRIVE_SYNCHRONIZATION_FOLDER}'",
            pageSize=10, fields="nextPageToken, files(id, name)").execute()
        # this gives us a list of all folders with that name
        folderIdResult = folderId.get('files', [])
        # however, we know there is only 1 folder with that name, so we just get the id of the 1st item in the list
        id = folderIdResult[0].get('id')
        return id

    def query_files_from_folder(self):
        try:
            folder_id=self.query_folder()
            # Now, using the folder ID gotten above, we get all the files from
            # that particular folder
            results = self.service.files().list(q="'" + folder_id + "' in parents", pageSize=10,
                                           fields="nextPageToken, files(id, name, modifiedTime, md5Checksum)").execute()
            items = results.get('files', [])
            for item in items:
                item['modifiedTime'] = get_date_object(item['modifiedTime'])
            return {item['name']: item for item in items}

        except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
            print(f'An error occurred: {error}')
            return []

    def upload_file(self, key, drive_files: Dict, files: Dict):
        folder_id = self.query_folder()
        last_mod_time = os.path.getmtime(files[key]['path'])
        file_metadata = {'name': f"{key}",
                         'parents': [folder_id],
                         'createdTime': get_date_string(last_mod_time),
                         'modifiedTime': get_date_string(last_mod_time)}
        media = MediaFileUpload(f'{files[key]["path"]}',
                                mimetype='application/octet-stream')
        # pylint: disable=maybe-no-member
        file = self.service.files().create(body=file_metadata, media_body=media,
                                           fields='id').execute()
        return file

    def update_file(self,key, drive_files: Dict, files:Dict):
        # File's new content.

        media_body = MediaFileUpload(
            files[key]['path'], mimetype='application/octet-stream')
        last_mod_time = os.path.getmtime(files[key]['path'])
        file_metadata = {'name': f"{key}",
                         #'parents': [self.query_folder()],
                         #'createdTime': get_date_string(last_mod_time),
                         #'modifiedTime': get_date_string(last_mod_time)
                         }

        # Send the request to the API.
        updated_file = self.service.files().update(
            fileId=drive_files[key]['id'],
            body=file_metadata,
            media_body=media_body,
            #setModifiedDate=True
        ).execute()
        return updated_file

    def download_file(self,key, drive_files: Dict, files: Dict, save_folder: Path):
        request = self.service.files().get_media(fileId=drive_files[key]['id'])
        file_bytes = io.BytesIO()
        downloader = MediaIoBaseDownload(file_bytes, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(F'Download {int(status.progress() * 100)}.')
        with open(save_folder / key,'wb') as f:
            f.write(file_bytes.getbuffer().tobytes())
        return request

