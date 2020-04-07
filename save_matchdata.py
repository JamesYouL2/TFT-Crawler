import pandas as pd 
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

#Get all json in array
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

#get traits and units and items
traits = pd.json_normalize(allrecords, 
record_path=['participants','traits'],
meta=['match_id',['participants','placement'],['participants','puuid']])
 
units = pd.json_normalize(allrecords,
record_path=['participants','units'],
meta=['match_id',['participants','placement'],['participants','puuid']])

items = pd.json_normalize(allrecords,
record_path=['participants','units', 'items'],
meta=['match_id',['participants','placement'],['participants','puuid']])
items.rename(columns={0: "item"},inplace=True)
items['count']=1
items=items.loc[items['item']>10]
items=items.merge(pd.read_json('items.json'),left_on='item',right_on='id')

#Pivot and combine spreadsheets
unitspivot=pd.pivot_table(units,index=['match_id','participants.placement'], columns='character_id',values='tier')
traitspivot=pd.pivot_table(traits,index=['match_id','participants.placement'], columns='name',values='tier_current')
itemspivot=pd.pivot_table(items,index=['match_id','participants.placement'], columns='name',values='count',aggfunc=np.sum)

#combinepivot = unitspivot.join(traitspivot).reset_index()
combinepivot = itemspivot.join(unitspivot.join(traitspivot)).reset_index()

#Only get most recent game version
df=pd.json_normalize(allrecords)
df=df.loc[df['game_version']==df['game_version'].max()]
#print(df['game_datetime'].apply(lambda x: datetime.datetime.fromtimestamp(x / 1e3).day).value_counts())

clusterdf=combinepivot.merge(df,on='match_id')[combinepivot.columns]

#HDB Scan
hdb = hdbscan.HDBSCAN(min_cluster_size=
int(np.floor(len(clusterdf)/10)), 
min_samples=1,
cluster_selection_method='eom')

unitscol=list(unitspivot.columns)
traitscol=list(traitspivot.columns)

cols = unitscol + traitscol

#print(cols)
print('HDB Scan')

clusterer=hdb.fit(clusterdf[cols].fillna(0))
clusterdf['hdb'] = pd.Series(hdb.labels_+1, index=clusterdf.index)
plot = clusterer.condensed_tree_.plot(select_clusters=True)

print(clusterdf['hdb'].value_counts())
print(clusterdf.groupby('hdb')[unitscol].count().idxmax(axis=1))
print(clusterdf.groupby('hdb')[traitscol].mean().idxmax(axis=1))
print(clusterdf.groupby('hdb')['participants.placement'].mean())

allhdbdf = pd.DataFrame()

#Create spreadsheet for MarkDown
for i in clusterdf.groupby('hdb')['participants.placement'].mean().sort_values().index:
    if (i != 0):
        rawhdbdf=pd.DataFrame(clusterdf[unitscol][clusterdf['hdb']==i].count().sort_values(ascending=False))
        rawitemsdf=pd.DataFrame(clusterdf[list(itemspivot.columns)][clusterdf['hdb']==i].count().sort_values(ascending=False))
        itemdf= (100* rawitemsdf / (clusterdf['hdb']==i).sum()).round().head(20).reset_index()
        hdbdf= (100* rawhdbdf / (clusterdf['hdb']==i).sum()).round().head(15).reset_index()
        hdbdf.loc[-1] = ['Placement',round(clusterdf[clusterdf['hdb']==i]['participants.placement'].mean(),2)]
        hdbdf.columns=[str(i)+'_character',str(i)+'_pct']
        itemdf.columns = hdbdf.columns
        itemdf.index=itemdf.index+100
        hdbitemdf = pd.concat([hdbdf,itemdf])
        allhdbdf = pd.concat([allhdbdf,hdbitemdf],axis=1)

#Export to MarkDown
with open('docs/tierlist.md','w') as tierlist:
    writer = csv.writer(tierlist)
    writer.writerow([df['game_version'].max()])
    tierlist.write('\n')
    writer.writerow([str(datetime.datetime.fromtimestamp(df['game_datetime'].max()/1e3))])
    tierlist.write('\n')
    allhdbdf.sort_index().to_markdown(tierlist)
    tierlist.write('\n')