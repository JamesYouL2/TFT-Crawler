import psycopg2
import configparser
import requests
import time
from pathlib import Path
import pandas as pd
import psycopg2.extras

connection = psycopg2.connect(
    host = 'tftcrawlerdb.cy9o9ix52yor.us-west-2.rds.amazonaws.com',
    port = 5432,
    user = 'tftcrawleruser',
    password = 'unrealtft',
    database = 'tftcrawlerdb'
    )
cursor=connection.cursor()

#creating table passengers
cursor.execute("""DROP TABLE IF EXISTS LadderNames""")

cursor.execute("""CREATE TABLE IF NOT EXISTS LadderNames(
id SERIAL PRIMARY KEY,
summonerName text,
region text)""")

connection.commit()

# using pandas to execute SQL queries



sql = """
SELECT "table_name","column_name", "data_type", "table_schema"
FROM INFORMATION_SCHEMA.COLUMNS
WHERE "table_schema" = 'public'
ORDER BY table_name  
"""
pd.read_sql(sql, con=connection)

config = configparser.ConfigParser()
config.read('config.ini')
key = configparser.ConfigParser()
key.read('keys.ini')

regions = config.get('adjustable', 'regions').split(',')
leagues = config.get('adjustable', 'leagues').split(',')

#Path(config.get('setup', 'ladder_dir')).mkdir(parents=True, exist_ok=True)

url = config.get('default', 'ladder_url').format(region, league, key.get('setup', 'api_key'))
response = requests.get(url)
response.raise_for_status()
entries = response.json()['entries']

entrylist=[(entry['summonerName'],'na') for entry in entries]

data = [(1,'x'), (2,'y')]
insert_query = 'insert into LadderNames (summonerName, region) values %s'
psycopg2.extras.execute_values (
    cursor, insert_query, entrylist, template=None, page_size=100
)

print

for region in regions:
    file = open(config.get('setup', 'ladder_dir') + '/ladder-{}.txt'.format(region), "w", encoding="utf-8")
    for league in leagues:
        url = config.get('default', 'ladder_url').format(region, league, key.get('setup', 'api_key'))
        print(url)
        try:
            response = requests.get(url)
            response.raise_for_status()
            if (response.status_code == 200):
                entries = response.json()['entries']
                
        except:
            print("something failed")
        time.sleep(.1)