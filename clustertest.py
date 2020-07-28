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

df = loaddb(hours=24)
gameversion = df['game_version'].max()

df=df.loc[df['game_version']==gameversion]

assert len(df) >= 100, "less than 100 matches in newest patch"

#Cluster Data
clusterclass=TFTClusterer(df)
#clusterclass.imputetraits()
clusterclass.reduce_dimension()
clusterclass.cluster(divisor=30, cluster_selection_epsilon=50)

clusterclass.eval_clustering()
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
