import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from config.definitions import DRIVE_ID, DIGEST_DRIVE_FOLDER_ID

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']

class DriveHelper():
  def __init__(self):
    DriveService = None

  def authenticate(self):
    creds = None

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
      creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
      if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
      else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)

      # Save the credentials for the next run
      with open('token.json', 'w') as token:
        token.write(creds.to_json())

    try:
      # Get drive service
      self.DriveService = build('drive', 'v3', credentials=creds)
      return True

      # Call the Drive v3 API
      results = self.DriveService.files().list(pageSize=10, fields="nextPageToken, files(id, name)").execute()
      items = results.get('files', [])

      if not items:
        print('No files found.')
        return

      print('Files:')
      for item in items:
        print(u'{0} ({1})'.format(item['name'], item['id']))

    except HttpError as error:
      # TODO Handle errors from drive API.
      print(f'An error occurred: {error}')
      return False

  def create_folder(self, folderName, parentId):
    # check if folder exists
    fileId = self.get_folder_id(self.DriveService, folderName, parentId)
    if not fileId == "":
      return fileId

    try:
      # create file data
      file_metadata = {
        'name': folderName,
        'mimeType': 'application/vnd.google-apps.folder'
      }

      # pylint: disable=maybe-no-member
      file = self.DriveService.files().create(body=file_metadata, fields='id').execute()
      print(f'Created folder in Google drive, id: {file.get("id")}')
      return file.get('id')

    except HttpError as error:
      print(f'An error occurred: {error}')
      return ""
    
  def get_folder_id(self, name, parentId):
    # query for folders with the specified name
    response = self.DriveService.files().list(
      q = f"name='{name}' and '{parentId}' in parents and mimeType='application/vnd.google-apps.folder'",
      driveId = DRIVE_ID,
      corpora ='drive',
      fields = 'files(id, name)',
      includeItemsFromAllDrives = True,
      supportsAllDrives = True
    ).execute()

    # check if a folder with a matching name exists
    folders = response.get('files', [])
    if len(folders) > 0:
      return folders[0].get('id')
    else:
      return ''

  def upload_gif(self, path, name, parentId):
    gfile = self.DriveService.CreateFile({
      'parents': [{'id': parentId}]
    })

    gfile.SetContentFile(path)
    gfile.Upload()

    try:
      file_metadata = {'name': name}
      media = MediaFileUpload(name, mimetype='image/gif')
      
      # pylint: disable=maybe-no-member
      file = self.DriveService.files().create(
        body=file_metadata, media_body=media, fields='id').execute()
      
      print(f'Uploaded file {name}, id: {file.get("id")}')
      return file.get('id')

    except HttpError as error:
      print(F'An error occurred: {error}')
      file = None
      return ""