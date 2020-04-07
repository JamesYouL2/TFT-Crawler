import pandas as pd 
from pandas import json_normalize    
import json
import datetime
import configparser
import json
import os
import requests
import numpy as np
import hdbscan
from dateutil import parser
import csv

config = configparser.ConfigParser()
config.read('config.ini')
regions = config.get('adjustable', 'regions').split(',')

allrecords = []
for region in regions:
    mintime = datetime.datetime.now() - datetime.timedelta(days=1)
    oslist=os.listdir(config.get('setup', 'raw_data_dir') + '/{}'.format(region))
    oslist.sort(reverse=True)
    for name in oslist:
        with open(config.get('setup', 'raw_data_dir') + '/{}/{}'.format(region, name), 'r', encoding="utf-8") as file: 
            data = json.load(file)
            s=data['game_datetime']
            date_time_obj = datetime.datetime.fromtimestamp(s / 1e3)
            if mintime > date_time_obj:
                break
            if data['queue_id'] != 1100:
                continue
            data.update({'match_id':name})
            allrecords.append(data)

#get traits and units
traits = json_normalize(allrecords, 
record_path=['participants','traits'],
meta=['match_id',['participants','placement'],['participants','puuid']])
 
units = json_normalize(allrecords,
record_path=['participants','units'],
meta=['match_id',['participants','placement'],['participants','puuid']])

items = json_normalize(allrecords,
record_path=['participants','units', 'items'],
meta=['match_id',['participants','placement'],['participants','puuid']])

unitspivot=pd.pivot_table(units,index=['match_id','participants.placement'], columns='character_id',values='tier')
traitspivot=pd.pivot_table(traits,index=['match_id','participants.placement'], columns='name',values='tier_current')

combinepivot = unitspivot.join(traitspivot).reset_index()

df=json_normalize(allrecords)
df=df.loc[df['game_version']==df['game_version'].max()]
print(df['game_datetime'].apply(lambda x: datetime.datetime.fromtimestamp(x / 1e3).day).value_counts())

clusterdf=combinepivot.merge(df,on='match_id')[combinepivot.columns]

hdb = hdbscan.HDBSCAN(min_cluster_size=
int(np.floor(len(clusterdf)/10)), 
min_samples=1,
cluster_selection_method='eom')

cols=list(clusterdf.columns)
cols.remove('match_id')
cols.remove('participants.placement')

#print(cols)
print('HDB Scan')

clusterer=hdb.fit(clusterdf[cols].fillna(0))
clusterdf['hdb'] = pd.Series(hdb.labels_+1, index=clusterdf.index)
plot = clusterer.condensed_tree_.plot(select_clusters=True)

unitscol=list(unitspivot.columns)
traitscol=list(traitspivot.columns)

print(clusterdf['hdb'].value_counts())
print(clusterdf.groupby('hdb')[unitscol].count().idxmax(axis=1))
print(clusterdf.groupby('hdb')[traitscol].mean().idxmax(axis=1))
print(clusterdf.groupby('hdb')['participants.placement'].mean())

allhdbdf = pd.DataFrame()

for i in clusterdf.groupby('hdb')['participants.placement'].mean().sort_values().index:
    if (i != 0):
        rawhdbdf=pd.DataFrame(clusterdf[unitscol][clusterdf['hdb']==i].count().sort_values(ascending=False))
        hdbdf= (100* rawhdbdf / (clusterdf['hdb']==i).sum()).round().head(10).reset_index()
        hdbdf.loc[-1] = ['Placement',round(clusterdf[clusterdf['hdb']==i]['participants.placement'].mean(),2)]
        hdbdf.columns=[str(i)+'_character',str(i)+'_pct']
        allhdbdf = pd.concat([allhdbdf,hdbdf],axis=1)

with open('docs/tierlist.md','w') as tierlist:
    writer = csv.writer(tierlist)
    writer.writerow([df['game_version'].max()])
    tierlist.write('\n')
    writer.writerow([str(datetime.datetime.fromtimestamp(df['game_datetime'].max()/1e3))])
    tierlist.write('\n')
    allhdbdf.sort_index().to_markdown(tierlist)
    tierlist.write('\n')