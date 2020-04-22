from riotwatcher import TftWatcher, ApiError
import pandas as pd
import configparser
import os
import psycopg2
import psycopg2.extras
from pantheon import pantheon
import asyncio
import nest_asyncio
import functools

nest_asyncio.apply()

#get config from text files
config = configparser.ConfigParser()
config.read('config.ini')

key = configparser.ConfigParser()
key.read('keys.ini')

loop = asyncio.get_event_loop()

#for debugging
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

#get tft watcher
#tft_watcher=TftWatcher(api_key=key.get('setup', 'api_key'))

#get all challenger summoner IDs and Summoner names
async def getchallengerladder(region, panth):
    try:
        data = await panth.getTFTChallengerLeague()
        ladder=pd.DataFrame(pd.json_normalize(data['entries'])[['summonerId','summonerName']])
        ladder['region']=region
        return ladder
    except Exception as e:
        print(e)

#Create db if does not yet exist
def createdbifnotexists():
    cursor=connection.cursor()
    cursor.execute("""DROP TABLE IF EXISTS LadderPuuid""")
    connection.commit()
    cursor.execute("""CREATE TABLE IF NOT EXISTS LadderPuuid(
    id SERIAL PRIMARY KEY,
    summonerName text,
    summonerId text,
    puuid text,
    region text)""")
    connection.commit()

#get cached data
def grabpuiiddb():
    cursor=connection.cursor()
    sql = """
    SELECT *
    FROM LadderPuuid
    """
    df=pd.read_sql(sql, con=connection)
    return df

#get all names without puuid
def getnameswithoutpuuid(region, panth):
    puuid = grabpuiiddb()
    asyncio.set_event_loop(asyncio.new_event_loop())
    ladder = asyncio.run(getchallengerladder(region, panth))
    summonernames = ladder[ladder.merge(puuid,left_on=['summonerId','region'], right_on=['summonerid','region'], how='left')['puuid'].isnull()]
    return summonernames

#call riot puuid
async def apipuuid(summonerids,region,panth):
    tasks = [panth.getTFTSummoner(summonerid) for summonerid in summonerids]
    return await asyncio.gather(*tasks)

async def insertpuuid(region, panth):
    summonernames = loop.run_in_executor(None,functools.partial(getnameswithoutpuuid,region=region,panth=panth))
    allpuuid=loop.run_until_complete(apipuuid(summonernames['summonerId'],region,panth))
    print(region)
    puuiddf=pd.json_normalize(allpuuid)[["name", "id", "puuid"]]
    puuiddf["region"]=region
    cursor=connection.cursor()
    query='INSERT INTO LadderPuuid (summonerName, summonerId, puuid, region) VALUES (%s, %s, %s, %s)'
    psycopg2.extras.execute_batch(cursor,query,(list(map(tuple, puuiddf.to_numpy()))))
    connection.commit()

async def main():
    createdbifnotexists()
    regions = config.get('adjustable', 'regions').split(',')
    tasks = []
    for region in regions:
        panth = pantheon.Pantheon(region, key.get('setup', 'api_key'), errorHandling=True, debug=True)
        tasks.append(insertpuuid(region, panth))
    await asyncio.gather(*tuple(tasks))
    #connection.close()

#if __name__ == "__main__":
    # execute only if run as a script
    #print("loadpuuid")
    #main() 