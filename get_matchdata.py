import configparser
import json
import time
import pandas as pd
import requests
from datetime import datetime, timedelta
from os import listdir
from os.path import isfile, join
import numpy as np
from pathlib import Path
import sys

config = configparser.ConfigParser()
config.read('config.ini')

key = configparser.ConfigParser()
key.read('keys.ini')

regions = config.get('adjustable', 'regions').split(',')

for region in regions:
    matchhistoryfile = config.get('setup','ladder_dir') + '/matchhistory- {}.txt'.format(region)
    matchhistory = pd.read_csv(matchhistoryfile,header=None, names=['matchid'])

    gamespath = config.get('setup','raw_data_dir') + '/{}/'.format(region)
    Path(gamespath).mkdir(parents=True, exist_ok=True)

    onlyfiles = pd.DataFrame([f for f in listdir(gamespath) if isfile(join(gamespath, f))],columns=['matchid_fromfile'])
    if len(onlyfiles) > 0:
        onlyfiles['matchid_fromfile']=onlyfiles['matchid_fromfile'].str.split('.',expand=True)[0]

    common = pd.merge(matchhistory,onlyfiles,how='left',left_on='matchid',right_on='matchid_fromfile')
    common = common.loc[common['matchid_fromfile'].isnull()].sort_values('matchid',ascending=False)
    common = common.loc[common['matchid'].str.split('_',expand=True)[0]==region.upper()]

    #Get Length of JSON
    print(len(common))

    for index, row in common.iterrows():
        value = row['matchid']
        if region in ('na1', 'br1', 'la1', 'la2', 'oc1'):
            superregion = 'americas'
        if region in ('eun1', 'euw1', 'ru', 'tr1'):
            superregion = 'europe'
        if region in ('kr', 'jp1'):
            superregion = 'asia'
    
        url = config.get('default', 'matchid_url').format(superregion, value, key.get('setup', 'api_key'))
    
        try:
            response = requests.get(url,verify=False)
            if (response.status_code == 200):
                with open(config.get('setup', 'raw_data_dir') + '/{}/{}.json'.format(region,value), "w") as file:
                    file.write(json.dumps(response.json()['info']))
                    if(datetime.fromtimestamp(response.json()['info']['game_datetime'] / 1e3) < (datetime.now() - timedelta(days=2))):
                        break

            if (response.status_code == 429):
                time.sleep(120)

            if (response.status_code == (404)):
                print("404 Error")

            if (response.status_code not in (200,429,404)):
                print(response.status_code)
                break

        except:
            print("something failed")
            print(sys.exc_info())
            break
        
        time.sleep(.2)
