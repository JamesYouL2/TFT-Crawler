####
#2. Gets Puuids for Summoner Names in ladder
####
import configparser
import json
import time
import pandas as pd
import requests
import sys

config = configparser.ConfigParser()
config.read('config.ini')

key = configparser.ConfigParser()
key.read('keys.ini')

regions = config.get('adjustable', 'regions').split(',')

for region in regions:
    file = config.get('setup', 'ladder_dir') + '/ladder-{}.txt'.format(region)
    ladder = pd.read_csv(file, header=None, names=['summonerName'])
    puuidfile = config.get('setup', 'ladder_dir') + '/puuid-{}.txt'.format(region)
    puuid = pd.read_csv(puuidfile)
    common = ladder.merge(puuid,on=['summonerName'], how='left')
    common = common[common['puuid'].isnull()]
    common['puuid'] = common['puuid'].astype(str)
    for index, row in common.iterrows():
        value = row['summonerName']
        url = config.get('default', 'summoner_url').format(region, value, key.get('setup', 'api_key'))
        try:
            response = requests.get(url)
            if (response.status_code == 200):
                common.at[index, 'puuid']=response.json()['puuid']
            elif (response.status_code == 429):
                time.sleep(120)
            else:
                print(response.status_code)
                break
        except:
            print("something failed")
            print(sys.exc_info()[0])
            break
        time.sleep(.2)
    alldf=common.append(puuid).drop_duplicates('summonerName')
    alldf.to_csv(puuidfile,index=None)