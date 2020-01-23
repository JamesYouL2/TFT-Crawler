import configparser
import json
import time
import pandas as pd
import requests

config = configparser.ConfigParser()
config.read('config.ini')

regions = config.get('adjustable', 'regions').split(',')

for region in regions:
    file = config.get('setup', 'ladder_dir') + '/ladder-{}.txt'.format(region)
    ladder = pd.read_csv(file, header=None, names=['summonerName'])
    
    puuidfile = config.get('setup', 'ladder_dir') + '/puuid-{}.txt'.format(region)
    puuid = pd.read_csv(puuidfile)

    matchhistoryfile = config.get('setup','ladder_dir') + '/matchhistory-{}.txt'.format(region)
    matchhistory = pd.read_csv(matchhistoryfile)

    matchhistorydatefile = config.get('setup','ladder_dir') + '/matchhistorydate-{}.txt'.format(region)
    matchhistorydate = pd.read_csv(matchhistorydatefile)

    common = ladder.merge(puuid,on=['summonerName'], how='left')
    common = common.merge(puuid,on='puuid',how='left')
    common = common[common['puuid'].isnull()]
    
    for index, row in common.iterrows():
        value = row['summonerName']
        
        if region in ('NA1', 'BR1', 'LA1', 'LA2', 'OC1'):
            superregion = 'americas'
        
        if region in ('EUN1', 'EUW1', 'RU', 'TR1'):
            superregion = 'europe'
        
        if region in ('KR', 'JP'):
            superregion = 'asia'
        
        url = config.get('default', 'matches_url').format(superregion, value, config.get('setup', 'api_key'))
        
        try:
            response = requests.get(url)
            if (response.status_code == 200):
                common.at[index, 'matchhistorydate']=datetime.datetime.now()
        
            if (response.status_code == 429):
                time.wait(120)
        
            if (response.status_code not in (200,429)):
                print(response.status_code)
                break

        except:
            print("something failed")
            print(sys.exc_info()[0])
            break
        
        time.sleep(.2)

    alldf=common.append(puuid).drop_duplicates('summonerName')
    alldf.to_csv(puuidfile,index=None)