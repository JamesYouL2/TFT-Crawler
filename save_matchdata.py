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
    matchhistoryfile = config.get('setup','ladder_dir') + '/matchhistory-{}.txt'.format(region)
    matchhistory = pd.read_csv(matchhistoryfile, squeeze=True)
    mintime = datetime.datetime.now() - datetime.timedelta(days=1)
    oslist=os.listdir(config.get('setup', 'raw_data_dir') + '/{}'.format(region))
    intersectionset = sorted(set(list(matchhistory + '.json')).intersection(oslist),reverse=True)
    for name in intersectionset:
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
meta=['match_id',['participants','placement'],['participants','puuid'],['participants','units','character_id']])
items.rename(columns={0: "item"},inplace=True)
items['count']=1
items=items.loc[items['item']>10]
items=items.merge(pd.read_json('items.json'),left_on='item',right_on='id')

#Pivot and combine spreadsheets
unitspivot=pd.pivot_table(units,index=['match_id','participants.placement'], columns='character_id',values='tier')
traitspivot=pd.pivot_table(traits,index=['match_id','participants.placement'], columns='name',values='tier_current')
#itemspivot=pd.pivot_table(items,index=['match_id','participants.placement'], columns=['name','participants.units.character_id'],values='count',aggfunc=np.sum)

#combinepivot = unitspivot.join(traitspivot).reset_index()
combinepivot = unitspivot.join(traitspivot).reset_index()

print(combinepivot)

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
#Cluster HDB
print('HDB Scan')
clusterer=hdb.fit(clusterdf[cols].fillna(0))
clusterdf['hdb'] = pd.Series(hdb.labels_+1, index=clusterdf.index)
plot = clusterer.condensed_tree_.plot(select_clusters=True)

print(clusterdf['hdb'].value_counts())
print(clusterdf.groupby('hdb')[unitscol].count().idxmax(axis=1))
print(clusterdf.groupby('hdb')[traitscol].mean().idxmax(axis=1))
print(clusterdf.groupby('hdb')['participants.placement'].mean())

#Merge items with HDB
itemshdb=items.merge(clusterdf)[list(items.columns)+list(['hdb'])]

allhdbdf = pd.DataFrame()

#Create spreadsheet for MarkDown
for i in clusterdf.groupby('hdb')['participants.placement'].mean().sort_values().index:
    if (i != 0):
        rawhdbdf=pd.DataFrame(clusterdf[unitscol][clusterdf['hdb']==i].count().sort_values(ascending=False))
        #get 15 most popular items per unit
        rawitemdf=itemshdb[itemshdb['hdb']==i].groupby(['name','participants.units.character_id']).count()['count'].sort_values(ascending=False).head(15).reset_index()
        #get 15 most popular units
        hdbdf= (100* rawhdbdf / (clusterdf['hdb']==i).sum()).round().head(15).reset_index()
        hdbdf.loc[-2] = ['Count',len(clusterdf[clusterdf['hdb']==i])]
        hdbdf.loc[-1] = ['Placement',round(clusterdf[clusterdf['hdb']==i]['participants.placement'].mean(),2)]
        hdbdf.columns=[str(i)+'_character',str(i)+'_pct']
        rawitemdf['character']=rawitemdf['participants.units.character_id']+rawitemdf['name']
        itemdf=rawitemdf[['character','count']]
        itemdf['count']= (100* itemdf['count']/ (clusterdf['hdb']==i).sum()).round()
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