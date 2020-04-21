from riotwatcher import TftWatcher, ApiError
import pandas as pd
import configparser
import os
import psycopg2
import psycopg2.extras

#get config from text files
config = configparser.ConfigParser()
config.read('config.ini')

key = configparser.ConfigParser()
key.read('keys.ini')

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
def getchallengerladder(region):
    testwatch=tft_watcher.league.challenger(region=region)
    ladder=pd.DataFrame(pd.json_normalize(testwatch['entries'])[['summonerId','summonerName']])
    ladder['region']=region
    return ladder

#Create db if does not yet exist
def createdbifnotexists():
    cursor=connection.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS LadderPuuid(
    id SERIAL PRIMARY KEY,
    summonerName text,
    summonerId text,
    puuid text,
    region text)""")
    connection.commit()

#get cached data
def grabladderdb():
    cursor=connection.cursor()
    sql = """
    SELECT *
    FROM LadderPuuid
    """
    df=pd.read_sql(sql, con=connection)
    return df

#get all names without puuid
def getnameswithoutpuuid(region):
    puuid = grabladderdb()
    ladder = getchallengerladder(region)
    summonernames = ladder[ladder.merge(puuid,left_on=['summonerId','region'], right_on=['summonerid','region'], how='left')['puuid'].isnull()]
    return summonernames

#insert records into database
def addpuuid(region):
    summonernames = getnameswithoutpuuid(region)
    for summid in summonernames['summonerId']:
        puuid=tft_watcher.summoner.by_id(region,summid)
        cursor=connection.cursor()
        cursor.execute('INSERT INTO LadderPuuid (summonerName, summonerId, puuid, region) VALUES (%s, %s, %s, %s)', (puuid["name"], puuid["id"], puuid["puuid"], region))
    connection.commit()

def main():
    for region in region:
        addpuuid(region)

if __name__ == "__main__":
    # execute only if run as a script
    main() 