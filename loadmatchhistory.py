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
import math

nest_asyncio.apply()

#get config from text files
config = configparser.ConfigParser()
config.read('config.ini')

key = configparser.ConfigParser() 
key.read('keys.ini')

#create loop
loop = asyncio.get_event_loop()

def requestsLog(url, status, headers):
    print(url[:100])
    #print(status)
    #print(headers)

#for debugging
region = "na1"
panth = pantheon.Pantheon(region, key.get('setup', 'api_key'), requestsLoggingFunction=requestsLog, errorHandling=True, debug=True)

#get puuidb first to see if async doesn't work
puuiddb = grabpuiiddb()


#connect to postgres database
connection = psycopg2.connect(
    host = key.get('database', 'host'),
    port = 5432,
    user = key.get('database', 'user'),
    password = key.get('database', 'password'),
    database = key.get('database', 'database')
    )

#Create db if does not yet exist
def creatematchhistorydbifnotexists():
    cursor=connection.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS MatchHistories(
    id SERIAL PRIMARY KEY,
    matchhistory json,
    matchhistoryid text,
    region text,
    date bigint,
    game_version text,
    queue_id int
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

async def runtasklist(tasks):
    data = pantheon.exc.RateLimit
    while data is pantheon.exc.RateLimit:
        try:
            asyncio.set_event_loop(asyncio.new_event_loop())
            task = asyncio.gather(*tasks, return_exceptions=True)
            data = await task
        except pantheon.exc.RateLimit as e:
            print('RateLimitException hit')
            time.sleep(120)
            print(data)
    return data

#call riot puuid
async def apigetmatchlist(puuids,panth):
    print("startmatchlist" + panth._server)
    tasks = [panth.getTFTMatchlist(puuid) for puuid in puuids]
    data = await (runtasklist(tasks))
    print("endmatchlist" + panth._server)
    return data

async def apigetmatch(matchhistoryids,panth):
    print("startmatches" + panth._server)
    tasks = [panth.getTFTMatch(matchhistoryid) for matchhistoryid in matchhistoryids]
    data = await (runtasklist(tasks))
    print("endmatches" + panth._server)
    return data

#get matchhistories to run through in sorted order
async def getpuuidtorun(panth):
    print('start'+panth._server)
    asyncio.set_event_loop(asyncio.new_event_loop())
    challenger = await getchallengerladder(panth)
    ladder = puuiddb.merge(challenger,left_on=["summonerid","region"],right_on=["summonerId","region"])
    print('ladder'+panth._server)
    return ladder
     
async def getmatchhistorylistfromapi(panth):
    puuidlist = await getpuuidtorun(panth)
    matchlists = await apigetmatchlist(puuidlist["puuid"],panth)
    flatmatchlist = [item for sublist in matchlists for item in sublist]
    allmatches = list(set(flatmatchlist))
    return allmatches

async def maxmatchhistory(days,panth):
    timestamp=(datetime.now() - timedelta(days=days)).timestamp()*1000
    cursor=connection.cursor()
    sql = """
    SELECT max(matchhistoryid)
    FROM MatchHistories
    where date > %s and region > %s
    """
    df=pd.read_sql(sql, con=connection, params=[timestamp,panth._server])
    return df['max'][0]

#delete match histories in database
async def cleanmatchhistorylist(panth):
    matchhistory = await getmatchhistorylistfromapi(panth)
    maxmatchhistoryid = await maxmatchhistory(days=2,panth=panth)
    if maxmatchhistoryid is not None:
        matchhistory = [i for i in matchhistory if i >= maxmatchhistoryid]
    dbmatchhistory = grabmatchhistorydb()
    return sorted(np.setdiff1d(matchhistory,dbmatchhistory).tolist(),reverse=True)

async def getmatchhistories(panth):
    allmatches = await cleanmatchhistorylist(panth)
    alljsons = list()
    for i in range(math.ceil(len(allmatches)/100)):
        matches = allmatches[i*100:(i*100)+100]
        matchjsons = await (apigetmatch(matches,panth))
        alljsons = alljsons + matchjsons
    return alljsons

def insertmatchhistories(matchhistoryjson):
    df=pd.json_normalize(matchhistoryjson)
    df["region"]=df["metadata.match_id"].str.split("_",expand=True)[0]
    df["json"]=df["info.participants"].apply(psycopg2.extras.Json)
    cursor=connection.cursor()
    insertdf=df[["json","metadata.match_id","region","info.game_datetime","info.game_variation","info.queue_id"]]
    query="INSERT INTO MatchHistories (matchhistory, matchhistoryid, region, date, game_version, queue_id) VALUES (%s, %s, %s, %s, %s, %s)"
    psycopg2.extras.execute_batch(cursor,query,(list(map(tuple, insertdf.to_numpy()))))
    connection.commit()

async def loadmatchhistories(panth):
    #print("start"+panth._server)
    jsoninsert=asyncio.run(getmatchhistories(panth))
    print("startinsert"+panth._server)
    insertmatchhistories(jsoninsert)
    print("end"+panth._server)

async def main():
    creatematchhistorydbifnotexists()
    regions = config.get('adjustable', 'regions').split(',')
    tasks = []
    for region in regions:
        panth = pantheon.Pantheon(region, key.get('setup', 'api_key'), errorHandling=True, debug=False)
        tasks.append(loadmatchhistories(panth))
    await asyncio.gather(*tuple(tasks))
    connection.close()