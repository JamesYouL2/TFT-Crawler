# To add a new cell, type ''
# To add a new markdown cell, type ' [markdown]'
import json
import pandas as pd
import hdbscan
import numpy as np
from TFTClusterer import TFTClusterer
from datetime import datetime, timedelta
from googledrivesave import trashfolder, outputtodrive
import pygsheets
from SQLGatherer import loaddb
from matplotlib import pyplot as plt


def main():
    #Grab Data
    df = loaddb(hours=24)
    df['patch_version'] = df['game_version'].str.split('.').str[:2].apply(lambda parts: ".".join(parts))
    patchversion = df['patch_version'].max()

    df=df.loc[df['patch_version']==patchversion]

    assert len(df) >= 100, "less than 100 matches in newest patch"

    #Cluster Data
    clusterclass=TFTClusterer(df, minunit = 1.33)
    #clusterclass.imputetraits()
    clusterclass.cluster(divisor=25, cluster_selection_epsilon=0)

    #Output cluster figure
    #clusterclass.reduce_dimension_graph()
    #clusterclass.eval_clustering()
    clusterclass.plot.figure.savefig('fig.png')
    pd.DataFrame(clusterclass.clusterdf.groupby('hdbnumber')['hdb'].value_counts()).to_csv('hdbnumber.csv')
    print(sum(clusterclass.clusterdf['hdbnumber']==0)/len(clusterclass.clusterdf))


    #output Files for Power BI
    clusterclass.unitshdb.to_csv("unitshdb.csv",index=False)
    clusterclass.itemshdb.to_csv("itemshdb.csv",index=False)
    clusterclass.clusterdf[["comp_id","participants.placement","hdb","game_variation"]].to_csv("hdb.csv",index=False)

    #Write newest date
    f = open('newestdate.csv','w')
    f.write(str(datetime.fromtimestamp(df['game_datetime'].max()/1e3))) #Give your csv text here.
    f.close()

    #Output files to drive for deracher
    allhdbdf = clusterclass.allhdbdf()

    variationname = 'AllGalaxies'
    trashfolder()

    outputtodrive(allhdbdf.sort_index(),variationname)

    outputtodrive(pd.DataFrame(data={'last_datetime': [df['game_datetime'].max()]}),'last_datetime')
    outputtodrive(pd.DataFrame(df['game_variation'].value_counts()),'gamevariationcounts')

