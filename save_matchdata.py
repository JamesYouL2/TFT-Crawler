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
    
    allhdbdf = clusterclass.allhdbdf()

    variationname = 'AllGalaxies'

    outputtodrive(allhdbdf.sort_index(),variationname)
    str(datetime.fromtimestamp(df['game_datetime'].max()/1e3))

    outputtodrive(pd.DataFrame(data={'last_datetime': [df['game_datetime'].max()]}),'last_datetime')
    outputtodrive(pd.DataFrame(df['game_variation'].value_counts()),'gamevariationcounts')
