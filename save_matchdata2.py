# To add a new cell, type ''
# To add a new markdown cell, type ' [markdown]'
import json
import pandas as pd
import hdbscan
import numpy as np
from TFTClusterer import TFTClusterer
from save_matchdata import loaddb
from datetime import datetime, timedelta
from googledrivesave import trashfolder, outputtodrive
import pygsheets

def main():
    df = loaddb(timestamp=(datetime.now() - timedelta(hours=4)).timestamp()*1000)
    gameversion = df['game_version'].max()

    df=df.loc[df['game_version']==gameversion]

    assert len(df) >= 100, "less than 100 matches in newest patch"

    clusterclass=TFTClusterer(df)

    clusterclass.cluster(divisor=25)

    clusterclass.unitshdb.to_csv("unitshdb.csv",index=False)
    clusterclass.itemshdb.to_csv("itemshdb.csv",index=False)
    clusterclass.clusterdf[["comp_id","participants.placement","hdb","game_variation"]].to_csv("hdb.csv",index=False)
    
    gc = pygsheets.authorize(service_file='./googlesheet.json')
    sh = gc.open('TFTSheets')

    allhdbdf = clusterclass.allhdbdf()

    variationname = 'AllGalaxies'

    #check googlesheets
    try:
        wksheet=sh.worksheet_by_title(variationname)
    except:
        sh.add_worksheet(variationname)
        wksheet=sh.worksheet_by_title(variationname)
        
    #Update worksheets
    wksheet.clear()
    wksheet.set_dataframe(allhdbdf.sort_index(),(1,1))
    #trashfolder()
    outputtodrive(allhdbdf.sort_index(),variationname)

    wks=sh.worksheet_by_title('Notes')
    wks.update_value((1, 1), str(datetime.fromtimestamp(df['game_datetime'].max()/1e3)))
    wks.update_value((2, 1), gameversion)

    outputtodrive(pd.DataFrame(data={'last_datetime': [df['game_datetime'].max()]}),'last_datetime')
    outputtodrive(pd.DataFrame(df['game_variation'].value_counts()),'gamevariationcounts')
