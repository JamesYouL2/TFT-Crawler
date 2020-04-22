import pandas as pd
import configparser
import os
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from loadpuuid import getchallengerladder, grabpuiiddb
import numpy as np
from pantheon import pantheon
import asyncio
import nest_asyncio
import functools
import concurrent.futures
import time

#get config from text files
config = configparser.ConfigParser()
config.read('config.ini')

key = configparser.ConfigParser()
key.read('keys.ini')

region = "na1"
panth = pantheon.Pantheon(region, key.get('setup', 'api_key'), errorHandling=True, debug=True)

#connect to postgres database
connection = psycopg2.connect(
    host = key.get('database', 'host'),
    port = 5432,
    user = key.get('database', 'user'),
    password = key.get('database', 'password'),
    database = key.get('database', 'database')
    )

#Create db if does not yet exist
def createdbifnotexists():
    cursor=connection.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS MatchHistories(
    id SERIAL PRIMARY KEY,
    matchhistory json,
    matchhistoryid text,
    region text,
    date bigint,
    game_version text
    )""")
    connection.commit()

#get matchhistory data
def grabmatchhistorydb():
    cursor=connection.cursor()
    sql = """
    SELECT matchhistoryid
    FROM MatchHistories
    """
    dbmatchhistory=list(pd.read_sql(sql, con=connection))
    return dbmatchhistory

#Switch Region to Superregion because of API
def getsuperregion(region):    
    if region in ('na1', 'br1', 'la1', 'la2', 'oc1'):
        superregion = 'americas'
    
    if region in ('eun1', 'euw1', 'ru', 'tr1'):
        superregion = 'europe'
    
    if region in ('kr', 'jp'):
        superregion = 'asia'
    
    return superregion

#get matchhistories to run through in sorted order
def getmatchhistorylist():
    ladder = grabpuiiddb()
    allmatches = list()
    superregion = getsuperregion(region)
    challenger = asyncio.run(getchallengerladder(region, panth))
    for puuid in ladder["puuid"]:
        matchlist = tft_watcher.match.by_puuid(superregion,puuid,100)
        allmatches = list(set(matchlist + allmatches))
    
    return sorted(allmatches, reverse=True)

#delete match histories in database
def cleanmatchhistorylist(region):
    matchhistory = getmatchhistorylist(region)
    dbmatchhistory=grabmatchhistorydb()
    return np.setdiff1d(matchhistory,dbmatchhistory).tolist()

def getmatchhistories(region):
    allmatches=getmatchhistorylist(region)
    cursor=connection.cursor()
    superregion = getsuperregion(region)
    for match in allmatches:
        df = pd.json_normalize(tft_watcher.match.by_id(superregion,match)['info'])
        if df["queue_id"] == 1100:
            cursor.execute('INSERT INTO MatchHistories (date, matchhistoryid, game_version, region, matchhistory) VALUES (%s, %s, %s, %s)' \
            , (df["game_datetime"], match, df["game_version"], region, df["participants"]))
        if (datetime.fromtimestamp(df['game_datetime'] / 1e3) < (datetime.now() - timedelta(days=1))):
            break