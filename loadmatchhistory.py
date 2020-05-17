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
import random
import sys

nest_asyncio.apply()

#get config from text files
config = configparser.ConfigParser()
config.read('config.ini')

key = configparser.ConfigParser() 
key.read('keys.ini')

#create loop
loop = asyncio.get_event_loop()

#connect to postgres database
connection = psycopg2.connect(
    host = key.get('database', 'host'),
    port = 5432,
    user = key.get('database', 'user'),
    password = key.get('database', 'password'),
    database = key.get('database', 'database')
    )
cursor=connection.cursor()

def requestsLog(url, status, headers):
    print(url[:100])
    #print(status)
    #print(headers)
    pass
    
#for debugging
region = "tr1"
panth = pantheon.Pantheon(region, key.get('setup', 'api_key'), requestsLoggingFunction=requestsLog, errorHandling=True, debug=True)

#Create db if does not yet exist
def creatematchhistorydbifnotexists():
    cursor.execute("""CREATE TABLE IF NOT EXISTS MatchHistories(
    id SERIAL PRIMARY KEY,
    participants json,
    match_id text,
    region text,
    game_datetime bigint,
    game_version text,
    game_variation text,
    queue_id int
    )""")
    connection.commit()

#get matchhistory data
def grabmatchhistorydb():
    sql = """
    SELECT match_id
    FROM MatchHistories
    """
    dbmatchhistory=list(pd.read_sql(sql, con=connection)['match_id'])
    return dbmatchhistory

#call api to get list of matches for each player
async def apigetmatchlist(puuids,panth):
    data = pantheon.exc.RateLimit
    #jitter the wait
    await asyncio.sleep(random.uniform(0,1))
    i = 1
    while type(data) == type and i < 60:
        try:
            #actually call matches
            tasks = [panth.getTFTMatchlist(puuid) for puuid in puuids]
            data = await asyncio.gather(*tasks, return_exceptions=False)
        except pantheon.exc.RateLimit as e:
            i = i + 1
            #print(e, str(i), panth._server)
            await asyncio.sleep(random.uniform(0,240))
        except:
            e = sys.exc_info()[0]
            print(panth._server, e, puuids)
            i = 1000
            data = None
    #assert i < 60
    return data

#call api to get matches
async def apigetmatch(matchhistoryids,panth):
    data = pantheon.exc.RateLimit
    #jitter the wait
    await asyncio.sleep(random.uniform(0,1))
    i = 1
    while type(data) == type and i < 60:
        try:
            tasks = [panth.getTFTMatch(matchhistoryid) for matchhistoryid in matchhistoryids]
            data = await asyncio.gather(*tasks, return_exceptions=False)
        except pantheon.exc.RateLimit as e:
            i = i + 1
            print(e, str(i), panth._server)
            await asyncio.sleep(random.uniform(0,240))
        except:
            e = sys.exc_info()[0]
            print(data, panth._server, e, matchhistoryids)
            i = 1000
            data = None
    #assert i < 60
    return data

#get matchhistories to run through in sorted order
async def getpuuidtorun(panth):
    #print('start'+panth._server)
    asyncio.set_event_loop(asyncio.new_event_loop())
    challenger = asyncio.run(getchallengerladder(panth))
    #get puuidb first to see if async doesn't work
    puuiddb = await grabpuiiddb()
    ladder = puuiddb.merge(challenger,left_on=["summonerid","region"],right_on=["summonerId","region"])
    ladder = ladder.loc[ladder['puuid'].notnull()]
    #print(str(len(ladder))+'ladder'+panth._server)
    return ladder

#wrapper to call api to get matchhistories
async def getmatchhistorylistfromapi(panth):
    puuidlist = await getpuuidtorun(panth)
    alllists = list()
    #start off randomly to not hit rate limit right away
    await asyncio.sleep(random.uniform(0,240))
    #split api calls into groups of 20
    for i in range(len(puuidlist)):
        puuids = puuidlist[i : i + 1]
        #print ("startmatchlist" + str(i) + panth._server)
        matchlists = await apigetmatchlist(puuids["puuid"],panth)
        if matchlists is not None:
            alllists = matchlists + alllists
    #matchlists = await apigetmatchlist(puuidlist["puuid"],panth)
    flatmatchlist = [item for sublist in alllists for item in sublist]
    allmatches = list(set(flatmatchlist))
    print ("donematchlist" + str(i) + panth._server)
    return allmatches

async def maxmatchhistorylessthandate(days,panth):
    timestamp=(datetime.now() - timedelta(days=days)).timestamp()*1000
    sql = """
    SELECT cast(max(substring(match_id,strpos(match_id,'_')+1,100)) as BIGINT)
    FROM MatchHistories
    where game_datetime < %(date)s and region = %(region)s
    """
    df=pd.read_sql(sql, con=connection, 
    params={"date":timestamp,"region":panth._server.upper()})
    #print(sql)
    return df['max'][0]

#delete match histories in database
async def cleanmatchhistorylist(panth, days):
    matchhistory = await getmatchhistorylistfromapi(panth)
    maxmatchhistoryid = await maxmatchhistorylessthandate(days=days,panth=panth)
    print(maxmatchhistoryid)
    if maxmatchhistoryid is not None:
        matchhistory = [i for i in matchhistory if int(i.split("_")[1]) >= int(maxmatchhistoryid)]
    dbmatchhistory = grabmatchhistorydb()
    return sorted(np.setdiff1d(matchhistory,dbmatchhistory).tolist(),reverse=True)

async def getmatchhistories(panth, days=2):
    allmatches = await cleanmatchhistorylist(panth,days)
    timestamp = (datetime.now() - timedelta(days=days)).timestamp()*1000
    #print("finishcleaning" + panth._server)
    alljsons = list()
    i = 0
    #alljsons = await apigetmatch(allmatches,panth)
    #split match history into parts to make it faster
    for i in range(len(allmatches)):
        matches = allmatches[i : i+1]
        #print ("startmatch" + str(i) + panth._server)
        matchjsons = await (apigetmatch(matches,panth))
        if matchjsons is None:
            continue
        insertmatchhistories(matchjsons)
        #print ("endmatch" + str(i) + panth._server)
        if (matchjsons[0]['info']['game_datetime'] < timestamp):
            break
    print("donematch" + str(i) + panth._server)
    return alljsons

def insertmatchhistories(matchhistoryjson):
    df=pd.json_normalize(matchhistoryjson)
    df["region"]=df["metadata.match_id"].str.split("_",expand=True)[0]
    df["json"]=df["info.participants"].apply(psycopg2.extras.Json)
    try:
        insertdf=df[["json","metadata.match_id","region","info.game_datetime","info.game_version","info.queue_id", "info.game_variation"]]
        query="INSERT INTO MatchHistories (participants, match_id, region, game_datetime, game_version, queue_id, game_variation) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        psycopg2.extras.execute_batch(cursor,query,(list(map(tuple, insertdf.to_numpy()))))
        connection.commit()
    except:
        print(df["metadata.match_id"])
        #print(Exception)

async def main():
    creatematchhistorydbifnotexists()
    regions = config.get('adjustable', 'regions').split(',')
    tasks = []
    for region in regions:
        panth = pantheon.Pantheon(
            region, 
            key.get('setup', 'api_key'), 
            #requestsLoggingFunction=requestsLog, 
            errorHandling=True, 
            #debug=True
            )
        tasks.append(getmatchhistories(panth))
    await asyncio.gather(*tuple(tasks))
    connection.close()

#test
async def test():
    regions = config.get('adjustable', 'regions').split(',')
    tasks = []
    for region in regions:
        panth = pantheon.Pantheon(
            region, 
            key.get('setup', 'api_key'), 
            #requestsLoggingFunction=requestsLog, 
            errorHandling=True, 
            #debug=True
            )
        tasks.append(getmatchhistories(panth))
    return await asyncio.gather(*tuple(tasks))

if __name__ == "__main__":
    creatematchhistorydbifnotexists()
    start=time.time()
    #time.sleep(120)
    print("loadmatchhistory")
    asyncio.run(main())
    #asyncio.run(getmatchhistories(panth))
    print((time.time()-start)/60)