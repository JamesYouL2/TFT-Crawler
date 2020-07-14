import pandas as pd
import configparser
from datetime import datetime, timedelta
import psycopg2

config = configparser.ConfigParser()
config.read('config.ini')
regions = config.get('adjustable', 'regions').split(',')

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

#Get all json in array
def loaddb(hours = 24, timestamp = None):
    if timestamp is None:
        timestamp=(datetime.now() - timedelta(hours=hours)).timestamp()*1000
    cursor=connection.cursor()
    sql = """
    SELECT *
    FROM MatchHistories where game_datetime > %(date)s
    """
    df=pd.read_sql(sql, con=connection, 
    params={"date":timestamp})
    return df