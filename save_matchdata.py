import pandas as pd 
from pandas.io.json import json_normalize    
import json
import datetime

patch_time = datetime.datetime.now() - datetime.timedelta(days=365)
with open('data/raw-games/na1/NA1_3353423535.json') as data_file:    
    data = json.load(data_file)

s=data['game_version']
date_time_str=s[s.find("(")+1:s.find(")")]
date_time_obj = datetime.datetime.strptime(date_time_str, '%b %d %Y/%H:%M:%S')
if date_time_obj > patch_time:
    patch_time = date_time_obj
if patch_time > date_time_obj:
    continue

participants = json_normalize(data,record_path=['participants'])
traits = json_normalize(data, 
record_path=['participants','traits'],
meta=[['participants','placement']])

champions = json_normalize(data,
record_path=['participants','champions'],
meta=['placement','puuid'])

pd.show_versions()