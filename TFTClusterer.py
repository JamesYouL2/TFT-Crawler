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

        traits=traits.merge(pd.read_json('traits.json'),left_on='name',right_on='key')
        traits['name']=traits['name_y']

        self.itemsdf = items
        self.unitsdf = units
        self.traitsdf = traits
        
        #Pivot and combine spreadsheets
        unitspivot=pd.pivot_table(units,index=['match_id','participants.placement', 'game_variation'], columns='character_id',values='tier')
        traitspivot=pd.pivot_table(traits,index=['match_id','participants.placement', 'game_variation'], columns='name',values='num_units')
        #itemspivot=pd.pivot_table(items,index=['match_id','participants.placement', 'game_variation'], columns=['participants.units.character_id'],values='count',aggfunc=np.sum)

        self.clusterdf = unitspivot.join(traitspivot).reset_index()

        self.unitscol=list(unitspivot.columns)
        self.traitscol=list(traitspivot.columns)
        self.itemscol=list(items.columns)

    def cluster(self, divisor = 30):
        #HDB Scan
        hdb = hdbscan.HDBSCAN(min_cluster_size=
        int(np.floor(len(self.clusterdf) / divisor)), 
        min_samples=1,
        cluster_selection_method='eom')

        cols = self.unitscol + self.traitscol

        #print(cols)
        #Cluster HDB
        print('HDB Scan')
        clusterer=hdb.fit(self.clusterdf[cols].fillna(0))
        self.plot = clusterer.condensed_tree_.plot(select_clusters=True)
        self.plot.figure
        self.clusterdf['hdbnumber'] = pd.Series(hdb.labels_+1, index=self.clusterdf.index)

        #Get top 2 traits
        commontraitsdf=self.clusterdf.fillna(0).groupby('hdbnumber')[self.traitscol].mean()
        commontraitslist=commontraitsdf.apply(lambda s: s.abs().nlargest(2).index.to_list(), axis=1)
        self.commontraits=commontraitslist.agg(lambda x: ' '.join(map(str, x)))
        self.commontraits[0]='No Comp'

        self.clusterdf=self.clusterdf.merge(pd.DataFrame({'hdb':self.commontraits}),left_on='hdbnumber',right_on='hdbnumber')
        self.clusterdf['comp_id'] = self.clusterdf['participants.placement'].apply(str)+self.clusterdf['match_id']

        self.traitshdb=self.traitsdf.merge(self.clusterdf)[list(self.traitsdf.columns)+list(['hdb'])+list(['comp_id'])]
        self.unitshdb=self.unitsdf.merge(self.clusterdf)[list(self.unitsdf.columns)+list(['hdb'])+list(['comp_id'])]
        self.itemshdb=self.itemsdf.merge(self.clusterdf)[list(self.itemsdf.columns)+list(['hdb'])+list(['comp_id'])]

        self.clusterdf=self.clusterdf.merge(pd.read_json('galaxies.json'),left_on='game_variation',right_on='key')[list(self.clusterdf.columns)+list(['name'])]
        self.clusterdf['game_variation']=self.clusterdf['name']
