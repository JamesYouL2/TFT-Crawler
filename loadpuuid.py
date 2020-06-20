import pandas as pd
import configparser
import os
import psycopg2
import psycopg2.extras
from pantheon import pantheon
import asyncio
import nest_asyncio
import functools
import concurrent.futures
import time
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

#for debugging
region = "kr"
panth = pantheon.Pantheon(region, key.get('setup', 'api_key'), errorHandling=True, debug=True)

#connect to postgres database
connection = psycopg2.connect(
    host = key.get('database', 'host'),
    port = 5432,
    user = key.get('database', 'user'),
    password = key.get('database', 'password'),
    database = key.get('database', 'database')
    )
cursor=connection.cursor()

#get tft watcher
#tft_watcher=TftWatcher(api_key=key.get('setup', 'api_key'))

#get all challenger summoner IDs and Summoner names
async def getchallengerladder(panth):
    data = pantheon.exc.RateLimit
    while type(data) == type:
        try:
            data = await panth.getTFTChallengerLeague()
            if len(data['entries']) > 0:
                ladder=pd.DataFrame(pd.json_normalize(data['entries'])[['summonerId','summonerName']])
                ladder['region']=panth._server
                return ladder
            else:
                ladder = pd.DataFrame(columns=['summonerId','summonerName','region'])
                return ladder
        except pantheon.exc.RateLimit as e:
            print(e, panth._server)
            await asyncio.sleep(random.uniform(0,240))       
        except Exception as e:
            raise e

async def getmasterladder(panth):
    data = pantheon.exc.RateLimit
    while type(data) == type:
        try:
            data = await panth.getTFTMasterLeague()
            if len(data['entries']) > 0:
                ladder=pd.DataFrame(pd.json_normalize(data['entries'])[['summonerId','summonerName']])
                ladder['region']=panth._server
                return ladder
            else:
                ladder = pd.DataFrame(columns=['summonerId','summonerName','region'])
                return ladder
        except pantheon.exc.RateLimit as e:
            print(e, panth._server)
            await asyncio.sleep(random.uniform(0,240))       
        except Exception as e:
            raise e

async def getgrandmasterladder(panth):
    data = pantheon.exc.RateLimit
    while type(data) == type:
        try:
            data = await panth.getTFTGrandmasterLeague()
            if len(data['entries']) > 0:
                ladder=pd.DataFrame(pd.json_normalize(data['entries'])[['summonerId','summonerName']])
                ladder['region']=panth._server
                return ladder
            else:
                ladder = pd.DataFrame(columns=['summonerId','summonerName','region'])
                return ladder
        except pantheon.exc.RateLimit as e:
            print(e, panth._server)
            await asyncio.sleep(random.uniform(0,240))       
        except Exception as e:
            raise e

#Create db if does not yet exist
def createdbifnotexists():
    #cursor.execute("""DROP TABLE IF EXISTS LadderPuuid""")
    connection.commit()
    cursor.execute("""CREATE TABLE IF NOT EXISTS LadderPuuid(
    id SERIAL PRIMARY KEY,
    summonerName text,
    summonerId text,
    puuid text,
    region text)""")
    connection.commit()

#get cached data
async def grabpuiiddb():
    sql = """
    SELECT *
    FROM LadderPuuid
    """
    df=pd.read_sql(sql, con=connection)
    return df

async def getmasterplus(panth):
    challenger = await getchallengerladder(panth)
    grandmaster = await getgrandmasterladder(panth)
    master = await getmasterladder(panth)
    return pd.concat([challenger, grandmaster, master])

#get all names without puuid
async def getnameswithoutpuuid(panth):
    puuid = await grabpuiiddb()
    ladder = await getmasterplus(panth)
    merged = ladder.merge(puuid,left_on=['summonerId','region'], right_on=['summonerid','region'],how='left')
    summonerids = merged[merged['puuid'].isnull()]['summonerId'].unique()
    print(panth._server+'SummonerIds:'+str(len(summonerids)))
    return summonerids

#call riot puuid
async def apipuuid(summonerid,panth):
    data = pantheon.exc.RateLimit
    #jitter the wait
    await asyncio.sleep(random.uniform(0,1))
    while type(data) == type:
        try:
            data = await panth.getTFTSummoner(summonerid)
        except pantheon.exc.RateLimit as e:
            print(e, panth._server)
            await asyncio.sleep(random.uniform(0,240))
        except:
            e = sys.exc_info()[0]
            raise e
    #assert i < 60
    return data

#wrapper to call api for summonerids to get puuids for and then insert
async def insertpuuid(panth):
    summonerids =  await getnameswithoutpuuid(panth)
    if len(summonerids)>0:
        for summonerid in summonerids:
            allpuuid = await apipuuid(summonerid,panth)
            puuiddf=pd.json_normalize(allpuuid)[["name", "id", "puuid"]]
            puuiddf["region"]=panth._server
            query='INSERT INTO LadderPuuid (summonerName, summonerId, puuid, region) VALUES (%s, %s, %s, %s)'
            psycopg2.extras.execute_batch(cursor,query,(list(map(tuple, puuiddf.to_numpy()))))
            connection.commit()

async def main():
    createdbifnotexists()
    regions = config.get('adjustable', 'regions').split(',')
    tasks = []
    for region in regions:
        panth = pantheon.Pantheon(region, key.get('setup', 'api_key'), errorHandling=True, debug=False)
        tasks.append(insertpuuid(panth))
    await asyncio.gather(*tuple(tasks))
    #connection.close()

if __name__ == "__main__":
    # execute only if run as a script
    start=time.time()
    print("loadpuuid")
    asyncio.run(main())
    print((time.time()-start)/60)