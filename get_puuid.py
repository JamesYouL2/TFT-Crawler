import configparser
import grequests
import math
import json
import time
import pandas as pd

config = configparser.ConfigParser()
config.read('config.ini')

regions = config.get('adjustable', 'regions').split(',')

for region in regions:
    file = config.get('setup', 'ladder_dir') + '/ladder-{}.txt'.format(region)
    ladder = pd.read_csv(file, header=None, names=['summonerName'])
    puuid = pd.read_csv(config.get('setup', 'ladder_dir') +
                        '/puuid-{}.txt'.format(region))
    for index, row in ladder.iterrows():
        value = row['summonerName']
        url = config.get('default', 'ladder_url').format(
            region, value, config.get('setup', 'api_key'))
        try:
			response = requests.get(url)
			if (response.status_code == 200):
                entries = response.json()['entries']
                row['puuid'] = entries['puuid']
	        except:
		    print("something failed")
		time.sleep(.1)
