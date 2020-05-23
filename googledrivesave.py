from pydrive.auth import GoogleAuth
import pandas as pd
from pydrive.drive import GoogleDrive

#outputs df to drive
def outputtodrive(df, variation):
    gauth = GoogleAuth()
    drive = GoogleDrive(gauth)

    gfile = drive.CreateFile({'title': variation + '.json', 'mimeType':'application/json',
            "parents": [{"kind": "drive#fileLink","id": '1VhfsK4QoMTZsFlcl44eIputhbVHsFb55'}]})

    gfile.SetContentString(df.to_json())
    gfile.Upload()

#Trash all files in folder
def trashfolder():
    gauth = GoogleAuth()
    drive = GoogleDrive(gauth)
    file_list = drive.ListFile({'q': "'1VhfsK4QoMTZsFlcl44eIputhbVHsFb55' in parents and trashed=false"}).GetList()
    for file1 in file_list:
        file1.Delete()