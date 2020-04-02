####
#3. Gets matches for Summoner Names in ladder
####
import configparser
import json
import time
import pandas as pd
import requests
import csv
from datetime import datetime, timedelta
from os import path

config = configparser.ConfigParser()
config.read('config.ini')

regions = config.get('adjustable', 'regions').split(',')

for region in regions:
    file = config.get('setup', 'ladder_dir') + '/ladder-{}.txt'.format(region)
    ladder = pd.read_csv(file, header=None, names=['summonerName'])
    
    #Load name and puuid file, create if doesn't exist
    puuidfile = config.get('setup', 'ladder_dir') + '/puuid-{}.txt'.format(region)
    if not path.exists(puuidfile):
        with open(puuidfile, 'w') as outcsv:
            writer = csv.writer(outcsv)
            writer.writerow(["summonerName", "puuid"])
    puuid = pd.read_csv(puuidfile)

    #Load file of match history IDa
    matchhistoryfile = config.get('setup','ladder_dir') + '/matchhistory-{}.txt'.format(region)
    if not path.exists(matchhistoryfile):
        with open(matchhistoryfile, 'w') as outcsv:
            writer = csv.writer(outcsv)
            writer.writerow(["matchhistory"])
    matchhistory = pd.read_csv(matchhistoryfile, squeeze=True)

    #Load file of puuids and when matchhistory was last updated
    matchhistorydatefile = config.get('setup','ladder_dir') + '/matchhistorydate-{}.txt'.format(region)
    if not path.exists(matchhistorydatefile):
        with open(matchhistorydatefile, 'w') as outcsv:
            writer = csv.writer(outcsv)
            writer.writerow(["date", "puuid"])
    matchhistorydate = pd.read_csv(matchhistorydatefile)

    #Get puuid for all master+ players
    common = ladder.merge(puuid,on=['summonerName'], how='left')
    #Get Correct Date
    common = common.merge(matchhistorydate,on='puuid',how='left')

    common['date'] = common['date'].fillna(value=datetime.now() - timedelta(days=365))
    common = common.loc[pd.to_datetime(common['date']) < (datetime.now() - timedelta(days=2))]
    
    for index, row in common.iterrows():
        value = row['puuid']
        
        #Switch Region to Superregion because of NA API
        if region in ('na1', 'br1', 'la1', 'la2', 'oc1'):
            superregion = 'americas'
        
        if region in ('eun1', 'euw1', 'ru', 'tr1'):
            superregion = 'europe'
        
        if region in ('kr', 'jp'):
            superregion = 'asia'
        
        url = config.get('default', 'matches_url').format(superregion, value, config.get('setup', 'api_key'))
        
        try:
            response = requests.get(url)
            #Valid Response
            if (response.status_code == 200):
                #MatchHistory File gets Current Date
                common.at[index, 'date']=datetime.now()
                matchhistory=matchhistory.append(pd.Series(response.json()))
                matchhistory=pd.Series(matchhistory.unique())
            
            #Sleep if Time Out error
            if (response.status_code == 429):
                time.sleep(120)
            
            #Break if invalid response
            if (response.status_code not in (200,429)):
                print(response.status_code)
                break

        except:
            print("something failed")
            #print(sys.exc_info()[0])
            break
        
        time.sleep(.2)

    #Get File of Puuids
    matchhistorydate=common[['date','puuid']].append(matchhistorydate).drop_duplicates('puuid')
    matchhistorydate.to_csv(matchhistorydatefile,index=None)
    pd.Series(matchhistory.unique()).to_csv(matchhistoryfile,index=False)