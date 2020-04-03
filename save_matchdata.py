import pandas as pd 
from pandas.io.json import json_normalize    
import json
import datetime
import configparser
import json
import os
import requests
import numpy as np
import hdbscan
from dateutil import parser

config = configparser.ConfigParser()
config.read('config.ini')
regions = config.get('adjustable', 'regions').split(',')

allrecords = []
for region in regions:
    mintime = datetime.datetime.now() - datetime.timedelta(days=14)
    for name in os.listdir(config.get('setup', 'raw_data_dir') + '/{}'.format(region)):
        with open(config.get('setup', 'raw_data_dir') + '/{}/{}'.format(region, name), 'r', encoding="utf-8") as file: 
            data = json.load(file)
            s=data['game_version']
            date_time_str=s[s.find("(")+1:s.find(")")]
            date_time_obj = datetime.datetime.strptime(date_time_str, '%b %d %Y/%H:%M:%S')
            if mintime > date_time_obj:
                continue
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

unitspivot=pd.pivot_table(units,index=['match_id','participants.placement'], columns='character_id',values='tier')
traitspivot=pd.pivot_table(traits,index=['match_id','participants.placement'], columns='name',values='tier_current')

combinepivot = unitspivot.join(traitspivot).reset_index()

df=json_normalize(allrecords)
df=df.loc[df['game_version']==df['game_version'].max()]

combinepivot.merge(df,on='match_id')[combinepivot.columns]

hdb = hdbscan.HDBSCAN(min_cluster_size=
int(np.floor(len(combinepivot)/15)), 
min_samples=1,
cluster_selection_method='leaf')

cols=list(combinepivot.columns)

clusterer=hdb.fit(combinepivot)
combinepivot['hdb'] = pd.Series(hdb.labels_+1, index=combinepivot.index)
print(combinepivot['hdb'].value_counts())
plot = clusterer.condensed_tree_.plot(select_clusters=True,
                               selection_palette=sns.color_palette('deep', 8))
