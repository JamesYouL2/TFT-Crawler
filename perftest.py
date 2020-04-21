from loadpuuid import getnameswithoutpuuid
import configparser
import time
import requests 
from riotwatcher import TftWatcher
import logging

config = configparser.ConfigParser()
config.read('config.ini')

key = configparser.ConfigParser()
key.read('keys.ini')

#get tft watcher
tft_watcher=TftWatcher(api_key=key.get('setup', 'api_key'))

region = "euw1"

summonernames = getnameswithoutpuuid(region)

# You must initialize logging, otherwise you'll not see debug output.
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

for name in summonernames['summonerId']:
    start=time.time()
    url = config.get('default', 'summonerid_url').format(region, name, key.get('setup', 'api_key'))
    #print(url)
    try:
        response = requests.get(url,)
        if (response.status_code == 200):
            end=time.time()
            print(end-start)
        elif (response.status_code == 429):
            print("429")
            time.sleep(120)
        else:
            print(response.status_code)
            break
    except:
        print("something failed")
        #print(sys.exc_info()[0])
        break

for name in summonernames['summonerId']:
    start=time.time()
    puuid=tft_watcher.summoner.by_id(region,name)
    end=time.time()
    print(end-start)