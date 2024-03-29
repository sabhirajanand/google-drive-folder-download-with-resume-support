from __future__ import print_function
import io
import sys
import os.path
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import time
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaDownloadProgress
from googleapiclient.http import _retry_request
from googleapiclient import _helpers as util
import random

class MyMediaIoBaseDownload(MediaIoBaseDownload):
    @util.positional(3)
    def __init__(self, fd, request, chunksize=1024*1024,progress=0):
        self._fd = fd
        self._request = request
        self._uri = request.uri
        self._chunksize = chunksize
        self._progress = progress
        self._total_size = None
        self._done = False

        # Stubs for testing.
        self._sleep = time.sleep
        self._rand = random.random

        self._headers = {}
        for k, v in request.headers.items():
            # allow users to supply custom headers by setting them on the request
            # but strip out the ones that are set by default on requests generated by
            # API methods like Drive's files().get(fileId=...)
            if not k.lower() in ("accept", "accept-encoding", "user-agent"):
                self._headers[k] = v
        self._headers["range"] = "bytes=%d-" % (self._progress)
    

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive']


def gDriveDownloadfile(fileid,filename,gdservice,tempfile_stream=None):
    done = False
    fh=None
    if (tempfile_stream==None):   # checking if resumed
        fh = open(filename+".temp","ab+")
    else:
        fh = tempfile_stream
    try:
        request = gdservice.files().get_media(fileId=fileid)
        downloadedbytes = 0
        if (not (tempfile_stream == None)):
            downloadedbytes = tempfile_stream.tell()
            print("Resuming Download.................")
        else:                    
            print("Downloading.................")
        downloader = MyMediaIoBaseDownload(fh, request, chunksize=512000,progress=downloadedbytes)
        while done is False:
            stime=time.time()
            status, done = downloader.next_chunk()
            etime=time.time()
            #print("Download %d%%." % int(status.progress() * 100))
            downloaded = round((status.progress() * 100),2)
            sys.stdout.write("\r%s%% [%s%s]         %sKb/s       " % ("{:.2f}".format(downloaded),'=' * (int(downloaded/2)), ' ' * (50-(int(downloaded/2))), ("{:.2f}".format((512/(etime-stime)))) ) )
            sys.stdout.flush()
    except:
        print("An Error occured while downloading")

    fh.close()

    return done
        

def main(folder_id):
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
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('drive', 'v3', credentials=creds)
        folder_name = "Default"
        query = f"parents = '{folder_id}' and mimeType != 'application/vnd.google-apps.folder'"
        try:
            folder_name = service.files().get(fileId=folder_id).execute()['name']
            folder_name = folder_name[0:55]
            print("Downloading files from folder: ",folder_name)
            print("----------------------------------------------------------------------------------------------")
            if(not os.path.isdir(folder_name)):
                os.mkdir(folder_name)

        except:
            print("Error with code: FNFOGNE")
            return 

        results = service.files().list(pageSize = 1000,supportsAllDrives=True, includeItemsFromAllDrives=True, q=query, orderBy='name').execute()
        
        items = results.get('files', [])
        
        if not items:
            print('No files found.')
            return
        else:
            print(len(items), "files found.")

        for item in items:
            print(u'{0} ({1})'.format(item['name'][0:55], item['id']))
            os.chdir(folder_name)
            ext=''
            try:
                ext = item['name'][item['name'].rindex('.'):]
            except:
                pass
            newfile = (item['name'][0:55]+ext)

            if os.path.isfile(newfile):
                print("Files is already downloaded.")
            else:
                tempFileStream=None
                if(os.path.isfile(newfile+".temp")):
                    tempFileStream= open(newfile+".temp","ab+")
                if not gDriveDownloadfile(fileid=item['id'],filename=newfile,gdservice=service,tempfile_stream=tempFileStream):
                    print("File not downloaded completely.")
                    return "00X1"
                else:
                    os.rename(newfile+".temp",newfile)
                    print("File downloaded sucessfully.")
            os.chdir("..")

    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f'An error occurred: {error}')     


if __name__ == '__main__':
    folder_id="none"
    if len(sys.argv)>1:
        folder_id=sys.argv[1]
    else:
        folder_id = input("Enter folder id : ")

    if main(folder_id)=="00X1":
        print("Retrying after 2 minutes..............................................")
        time.sleep(60*2)
        os.chdir("..")
        os.system('python run.py "'+folder_id+'"')
        os.system("pause")
