import sys
sys.path.append("..")
import pandas as pd
import configparser
import loadpuuid
import loadmatchhistory
import asyncio
from pantheon import pantheon

def matches():
    key = configparser.ConfigParser()
    key.read('keys.ini')

    region = 'europe'
    panth = pantheon.Pantheon(region, key.get('setup', 'api_key'), errorHandling=True, debug=True)

    return asyncio.run(loadmatchhistory.cleanmatchhistorylist(panth, 'euw1', 1))

def testfn():
    testdb = matches()
    assert len(testdb) > 0