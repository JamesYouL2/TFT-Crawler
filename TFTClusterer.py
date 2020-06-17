import json
import pandas as pd
import hdbscan
import numpy as np

class TFTClusterer:
    def __init__(self, df):
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
        items=items.merge(pd.read_json('items.json'),left_on='item',right_on='id')

        self.itemsdf = items
        self.unitsdf = units
        self.traitsdf = traits

        #Pivot and combine spreadsheets
        unitspivot=pd.pivot_table(units,index=['match_id','participants.placement', 'game_variation'], columns='character_id',values='tier')
        traitspivot=pd.pivot_table(traits,index=['match_id','participants.placement', 'game_variation'], columns='name',values='tier_current')
        #itemspivot=pd.pivot_table(items,index=['match_id','participants.placement', 'game_variation'], columns=['participants.units.character_id'],values='count',aggfunc=np.sum)

        self.clusterdf = unitspivot.join(traitspivot).reset_index()

        self.unitscol=list(unitspivot.columns)
        self.traitscol=list(traitspivot.columns)
        self.itemscol=list(items.columns)

    def cluster(self):
        #HDB Scan
        hdb = hdbscan.HDBSCAN(min_cluster_size=
        int(np.floor(len(self.clusterdf) / 20)), 
        min_samples=1,
        cluster_selection_method='eom')

        cols = self.unitscol + self.traitscol

        #print(cols)
        #Cluster HDB
        print('HDB Scan')
        clusterer=hdb.fit(self.clusterdf[cols].fillna(0))
        self.clusterdf['hdb'] = pd.Series(hdb.labels_+1, index=self.clusterdf.index)
        #plot = clusterer.condensed_tree_.plot(select_clusters=True)

        self.traitshdb=self.traitsdf.merge(self.clusterdf)[list(self.traitsdf.columns)+list(['hdb'])]
        self.unitshdb=self.unitsdf.merge(self.clusterdf)[list(self.unitsdf.columns)+list(['hdb'])]
        self.itemshdb=self.itemsdf.merge(self.clusterdf)[list(self.itemsdf.columns)+list(['hdb'])]

        self.traitshdb['comp_id'] = self.traitshdb['participants.placement'].apply(str)+self.traitshdb['match_id']
        self.unitshdb['comp_id'] = self.unitshdb['participants.placement'].apply(str)+self.unitshdb['match_id']
        self.itemshdb['comp_id'] = self.itemshdb['participants.placement'].apply(str)+self.itemshdb['match_id']