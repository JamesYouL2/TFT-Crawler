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
    df=pd.read_sql(sql, con=connection)
    return df

#grab ladder records
def grabladderdb():
    cursor=connection.cursor()
    sql = """
    SELECT *
    FROM LadderPuuid
    """
    df=pd.read_sql(sql, con=connection)
    return df

#get matchhistories to run through
def getmatchhistorylist(region):
    #Switch Region to Superregion because of NA API
    if region in ('na1', 'br1', 'la1', 'la2', 'oc1'):
        superregion = 'americas'
    
    if region in ('eun1', 'euw1', 'ru', 'tr1'):
        superregion = 'europe'
    
    if region in ('kr', 'jp'):
        superregion = 'asia'
    
    ladder = grabladderdb()
    allmatches = list()

    for puuid in ladder['puuid']:
        matchlist = tft_watcher.match.by_puuid(superregion,puuid,100)
        allmatches = list(set(matchlist + allmatches))
    
    return allmatches

def 