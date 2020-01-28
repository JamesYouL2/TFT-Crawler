import configparser
import json
import time
import pandas as pd
import requests
from datetime import datetime, timedelta

config = configparser.ConfigParser()
config.read('config.ini')

regions = config.get('adjustable', 'regions').split(',')

for region in regions:
    file = config.get('setup', 'ladder_dir') + '/ladder-{}.txt'.format(region)
    ladder = pd.read_csv(file, header=None, names=['summonerName'])
    
    puuidfile = config.get('setup', 'ladder_dir') + '/puuid-{}.txt'.format(region)
    puuid = pd.read_csv(puuidfile)

    matchhistoryfile = config.get('setup','ladder_dir') + '/matchhistory-{}.txt'.format(region)
    matchhistory = pd.read_csv(matchhistoryfile, squeeze=True)

    matchhistorydatefile = config.get('setup','ladder_dir') + '/matchhistorydate-{}.txt'.format(region)
    matchhistorydate = pd.read_csv(matchhistorydatefile)

    common = ladder.merge(puuid,on=['summonerName'], how='left')
    common = common.merge(matchhistorydate,on='puuid',how='left')
    common['date'] = common['date'].fillna(value=datetime.now() - timedelta(days=365))
    common = common.loc[pd.to_datetime(common['date']) < (datetime.now() - timedelta(days=2))]
    
    for index, row in common.iterrows():
        value = row['puuid']
        
        if region in ('na1', 'br1', 'la1', 'la2', 'oc1'):
            superregion = 'americas'
        
        if region in ('eun1', 'euw1', 'ru', 'tr1'):
            superregion = 'europe'
        
        if region in ('kr', 'jp'):
            superregion = 'asia'
        
        url = config.get('default', 'matches_url').format(superregion, value, config.get('setup', 'api_key'))
        
        try:
            response = requests.get(url)
            if (response.status_code == 200):
                common.at[index, 'date']=datetime.now()
                matchhistory=matchhistory.append(pd.Series(response.json()))
                matchhistory=pd.Series(matchhistory.unique())
        
            if (response.status_code == 429):
                time.sleep(120)
        
            if (response.status_code not in (200,429)):
                print(response.status_code)
                break

        except:
            print("something failed")
            print(sys.exc_info()[0])
            break
        
        time.sleep(.2)

    matchhistorydate=common[['date','puuid']].append(matchhistorydate).drop_duplicates('puuid')
    matchhistorydate.to_csv(matchhistorydatefile,index=None)
    pd.Series(matchhistory.unique()).to_csv(matchhistoryfile,index=False)