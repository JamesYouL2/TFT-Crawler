import pandas as pd 
import json
from datetime import datetime, timedelta
import configparser
import json
import os
import requests
import numpy as np
import hdbscan
from dateutil import parser
import csv
import psycopg2
import time
import pygsheets

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
def loaddb(days):
    timestamp=(datetime.now() - timedelta(days=days)).timestamp()*1000
    cursor=connection.cursor()
    sql = """
    SELECT *
    FROM MatchHistories where game_datetime > %(date)s
    """
    df=pd.read_sql(sql, con=connection, 
    params={"date":timestamp})
    return df

#Clusters a dataframe and outputs data to markdown format
def tfthdb(clusterdf, name, unitscol, traitscol, items):
    #HDB Scan
    hdb = hdbscan.HDBSCAN(min_cluster_size=
    int(np.floor(len(clusterdf)/20)), 
    min_samples=1,
    cluster_selection_method='eom')

    cols = unitscol + traitscol

    #print(cols)
    #Cluster HDB
    print('HDB Scan')
    clusterer=hdb.fit(clusterdf[cols].fillna(0))
    clusterdf['hdb'] = pd.Series(hdb.labels_+1, index=clusterdf.index)
    plot = clusterer.condensed_tree_.plot(select_clusters=True)

    print(clusterdf['hdb'].value_counts())
    print(clusterdf.groupby('hdb')[unitscol].count().idxmax(axis=1))
    print(clusterdf.groupby('hdb')[traitscol].mean().idxmax(axis=1))
    print(clusterdf.groupby('hdb')['participants.placement'].mean())

    #Merge items with HDB
    itemshdb=items.merge(clusterdf)[list(items.columns)+list(['hdb'])]

    allhdbdf = pd.DataFrame()

    #Create spreadsheet for MarkDown
    for i in clusterdf.groupby('hdb')['participants.placement'].mean().sort_values().index:
        if (i != 0):
            rawhdbdf=pd.DataFrame(clusterdf[unitscol][clusterdf['hdb']==i].count().sort_values(ascending=False))
            #get 15 most popular items per unit
            rawitemdf=itemshdb[itemshdb['hdb']==i].groupby(['name','participants.units.character_id']).count()['count'].sort_values(ascending=False).head(25).reset_index()
            #get 15 most popular units
            hdbdf= (100* rawhdbdf / (clusterdf['hdb']==i).sum()).round().head(15).reset_index()
            hdbdf.loc[-2] = ['Count',len(clusterdf[clusterdf['hdb']==i])]
            hdbdf.loc[-1] = ['Placement',round(clusterdf[clusterdf['hdb']==i]['participants.placement'].mean(),2)]
            hdbdf.columns=[str(i)+'_character',str(i)+'_pct']
            rawitemdf['character']=rawitemdf['participants.units.character_id']+rawitemdf['name']
            itemdf=rawitemdf[['character','count']]
            itemdf['count']= (100* itemdf['count']/ (clusterdf['hdb']==i).sum()).round()
            itemdf.columns = hdbdf.columns
            itemdf.index=itemdf.index+100
            hdbitemdf = pd.concat([hdbdf,itemdf])
            allhdbdf = pd.concat([allhdbdf,hdbitemdf],axis=1)

    return allhdbdf
    

def main():
    df = loaddb(days = 2)
    
    df=df.loc[df['game_version'].str.rsplit('.',2).str[0]==df['game_version'].str.rsplit('.',2).str[0][len(df)-1]]

    assert len(df) >= 100, "less than 100 matches in newest patch"

    allrecords = df.to_json(orient='records')

    traits = pd.json_normalize(json.loads(allrecords), 
    record_path=['participants','traits'],
    meta=['match_id','game_variation',['participants','placement'],['participants','puuid']])
    
    units = pd.json_normalize(json.loads(allrecords), 
    record_path=['participants','units'],
    meta=['match_id','game_variation',['participants','placement'],['participants','puuid']])

    items = pd.json_normalize(json.loads(allrecords),
    record_path=['participants','units', 'items'],
    meta=['match_id','game_variation',['participants','placement'],['participants','puuid'],['participants','units','character_id']])

    items.rename(columns={0: "item"},inplace=True)
    items['count']=1
    #items=items.loc[items['item']>10]
    items=items.merge(pd.read_json('items.json'),left_on='item',right_on='id')

    #Pivot and combine spreadsheets
    unitspivot=pd.pivot_table(units,index=['match_id','participants.placement', 'game_variation'], columns='character_id',values='tier')
    traitspivot=pd.pivot_table(traits,index=['match_id','participants.placement', 'game_variation'], columns='name',values='tier_current')
    #itemspivot=pd.pivot_table(items,index=['match_id','participants.placement', 'game_variation'], columns=['participants.units.character_id'],values='count',aggfunc=np.sum)

    combinepivot = unitspivot.join(traitspivot).reset_index()

    unitscol=list(unitspivot.columns)
    traitscol=list(traitspivot.columns)
    itemscol=list(items.columns)

    assert combinepivot['game_variation'].value_counts().min() >= 100, "less than 100 records for variation"

    for variation in combinepivot['game_variation'].unique():
        #print(variation)
        variationdf = combinepivot.loc[combinepivot['game_variation']==variation]
        hdbdfvariation=tfthdb(variationdf, variation, unitscol, traitscol, items)
        variationname = variation[variation.rindex('_')+1:]
        
        gc = pygsheets.authorize(service_file='./googlesheet.json')
        sh = gc.open('TFTSheets')
        #check googlesheets
        try:
            wksheet=sh.worksheet_by_title(variationname)
        except:
            sh.add_worksheet(variationname)
            wksheet=sh.worksheet_by_title(variationname)
            
        #Update worksheets
        wksheet.clear()
        wksheet.set_dataframe(hdbdfvariation.sort_index(),(1,1))
    
    #update static values
    wks=sh.worksheet_by_title('Notes')
    wks.update_value((1, 1), str(datetime.fromtimestamp(df['game_datetime'].max()/1e3)))
    wks.update_value((2, 1), df['game_version'].str.rsplit('.',2).str[0][len(df)-1])

if __name__ == "__main__":
    # execute only if run as a script
    start=time.time()
    print("hdbscan")
    main()
    print((time.time()-start)/60)