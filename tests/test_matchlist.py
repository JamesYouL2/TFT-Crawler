import sys
sys.path.append("..")
import pandas as pd
import configparser
import loadpuuid
import loadmatchhistory
import asyncio
from pantheon import pantheon

def matchhistory():
    key = configparser.ConfigParser()
    key.read('keys.ini')

    region = 'europe'
    panth = pantheon.Pantheon(region, key.get('setup', 'api_key'), errorHandling=True, debug=True)
    puuids = ['TKln2rK8guuLVAsI0FZJFr6-13-H6n4KpRV08VffOvV3tg2utD1npfdEfGjJsWKd_-6-wo38fngSuA']
    
    return asyncio.run(loadmatchhistory.apigetmatchlist(puuids, panth))

def testfn():
    testdb = matchhistory()
    assert len(testdb) > 0