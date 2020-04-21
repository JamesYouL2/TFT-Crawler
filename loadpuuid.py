from riotwatcher import TftWatcher, ApiError
import pandas as pd
import configparser
import os
import psycopg2
import psycopg2.extras
from pantheon import pantheon
import asyncio
import nest_asyncio
nest_asyncio.apply()

#get config from text files
config = configparser.ConfigParser()
config.read('config.ini')

key = configparser.ConfigParser()
key.read('keys.ini')

loop = asyncio.get_event_loop()

#requestslog
def requestsLog(url, status, headers):
    print(url)
    print(status)
    print(headers)

#for debugging
region = "na1"
panth = pantheon.Pantheon(region, key.get('setup', 'api_key'), errorHandling=True, requestsLoggingFunction=requestsLog, debug=True)

#connect to postgres database
connection = psycopg2.connect(
    host = key.get('database', 'host'),
    port = 5432,
    user = key.get('database', 'user'),
    password = key.get('database', 'password'),
    database = key.get('database', 'database')
    )

#get tft watcher
tft_watcher=TftWatcher(api_key=key.get('setup', 'api_key'))

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
    ladder = getchallengerladder(region, panth)
    summonernames = ladder[ladder.merge(puuid,left_on=['summonerId','region'], right_on=['summonerid','region'], how='left')['puuid'].isnull()]
    return summonernames

#insert records into database
def getpuuid(region):
    summonernames = getnameswithoutpuuid(region)
    allpuuid=list()
    for summid in summonernames['summonerId']:
        #put call in try except block
        try:
            print(summid)
            puuid=tft_watcher.summoner.by_id(region,summid)
        except ApiError as err:
            if err.response.status_code == 429:
                print('We should retry in {} seconds.'.format(err.headers['Retry-After']))
                print('this retry-after is handled by default by the RiotWatcher library')
                print('future requests wait until the retry-after time passes')
            elif err.response.status_code == 404:
                print('Summoner with that ridiculous name not found.')
            else:
                raise
        allpuuid.append(puuid)
    return allpuuid

def insertpuuid(region, panth):    
    cursor=connection.cursor()
    query=('INSERT INTO LadderPuuid (summonerName, summonerId, puuid, region) VALUES (%s, %s, %s, %s)')
    getpuuid(region)
    connection.commit()

def main():
    createdbifnotexists()
    regions = config.get('adjustable', 'regions').split(',')
    for region in regions:
        panth = pantheon.Pantheon(region, key.get('setup', 'api_key'), errorHandling=True, requestsLoggingFunction=requestsLog, debug=True)
        insertpuuid(region, panth)
        print(region)
    connection.close()

if __name__ == "__main__":
    # execute only if run as a script
    print("loadpuuid")
    main() 