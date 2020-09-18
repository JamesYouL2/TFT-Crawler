import sys
sys.path.append("..")
import pandas as pd
import configparser
import loadpuuid
import loadmatchhistory
import asyncio
from pantheon import pantheon

key = configparser.ConfigParser()
key.read('keys.ini')

def matchhistory():
    region = 'europe'
    panth = pantheon.Pantheon(region, key.get('setup', 'api_key'), errorHandling=True, debug=True)
    puuids = ['TKln2rK8guuLVAsI0FZJFr6-13-H6n4KpRV08VffOvV3tg2utD1npfdEfGjJsWKd_-6-wo38fngSuA']
    testdb = asyncio.run(loadmatchhistory.apigetmatchlist(puuids, panth))
    assert len(testdb) > 0

def getmatchestorun():
    region = 'euw1'
    panth = pantheon.Pantheon('europe', key.get('setup', 'api_key'), errorHandling=True, debug=True)
    testdb = asyncio.run(loadmatchhistory.getmatchhistorylistfromapi(panth,region))
    assert len(testdb) > 0

def matches():
    panth = pantheon.Pantheon('europe', key.get('setup', 'api_key'), errorHandling=True, debug=True)
    matches = ['EUW1_4819630931']
    matchjsons = asyncio.run(loadmatchhistory.apigetmatch(matches,panth))
    assert len(matchjsons) > 0
    return matchjsons

def testinsert():
    testjsons = matches()
    loadmatchhistory.insertmatchhistories(testjsons)