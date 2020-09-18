import sys
sys.path.append("..")
import pandas as pd
import configparser
import loadpuuid
import asyncio
from pantheon import pantheon

def getladder():
    key = configparser.ConfigParser()
    key.read('keys.ini')
    
    config = configparser.ConfigParser()
    config.read('config.ini')

    regions = config.get('adjustable', 'regions').split(',')

    alldata = pd.DataFrame()

    for region in regions:
        print(region)
        panth = pantheon.Pantheon(region, key.get('setup', 'api_key'), errorHandling=True, debug=True)
        data = asyncio.run(loadpuuid.getmasterplus(panth))
        alldata=pd.concat([alldata, data])
    return alldata

def testfn():
    testdb = getladder()
    assert len(testdb) > 0