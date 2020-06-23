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

    def cluster(self, divisor = 25):
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
        self.plot = clusterer.condensed_tree_.plot(select_clusters=True, label_clusters=True)
        
        self.clusterdf['hdbnumber'] = pd.Series(hdb.labels_+1, index=self.clusterdf.index)
        self.clusterdf['comp_id'] = self.clusterdf['participants.placement'].apply(str)+self.clusterdf['match_id']
        
        #print(self.clusterdf['hdbnumber'].value_counts())

        #Get top 2 traits
        traitsaveragedf = self.clusterdf.fillna(0).groupby('hdbnumber')[list(self.traitscol)].mean()
        commontraitslist=traitsaveragedf.apply(lambda s: s.abs().nlargest(2).index.to_list(), axis=1)
        self.commontraits=commontraitslist.agg(lambda x: ' '.join(map(str, x)))
        self.commontraits[0]='No Comp'

        self.clusterdf=self.clusterdf.merge(pd.DataFrame({'hdb':self.commontraits}),left_on='hdbnumber',right_on='hdbnumber')        

        self.traitshdb=self.traitsdf.merge(self.clusterdf)[list(self.traitsdf.columns)+list(['hdb'])+list(['comp_id'])]
        self.unitshdb=self.unitsdf.merge(self.clusterdf)[list(self.unitsdf.columns)+list(['hdb'])+list(['comp_id'])]
        self.itemshdb=self.itemsdf.merge(self.clusterdf)[list(self.itemsdf.columns)+list(['hdb'])+list(['comp_id'])]

        self.clusterdf=self.clusterdf.merge(pd.read_json('galaxies.json'),left_on='game_variation',right_on='key',how='left')
        self.clusterdf['game_variation']=np.where(self.clusterdf['name'].notnull(),self.clusterdf['name'],self.clusterdf['game_variation'])
        self.clusterdf['game_variation']=np.where(self.clusterdf['game_variation']=='TFT3_GameVariation_LittlerLegends','Littler Legends',self.clusterdf['game_variation'])

    def allhdbdf(self):
        clusterdf = self.clusterdf
        unitscol = self.unitscol
        itemshdb = self.itemshdb

        allhdbdf=pd.DataFrame()
        count = 1

        for i in clusterdf.groupby('hdb')['participants.placement'].mean().sort_values().index:
            if (i != 'No Comp'):
                rawhdbdf=pd.DataFrame(clusterdf[unitscol][clusterdf['hdb']==i].count().sort_values(ascending=False))
                starsdf=pd.DataFrame(clusterdf[unitscol][clusterdf['hdb']==i].mean().round(2).sort_values(ascending=False)).rename(columns={0:"stars"})
                #get 15 most popular items per unit
                rawitemdf=itemshdb[itemshdb['hdb']==i].groupby(['name','participants.units.character_id']).count()['count'].sort_values(ascending=False).head(25).reset_index()
                #get 15 most popular units
                hdbdf= (100* rawhdbdf / (clusterdf['hdb']==i).sum()).round().head(15).rename(columns={0:"percent"})
                #combine unit percent and unit stars
                hdbdf = hdbdf.merge(starsdf, left_index=True, right_index=True).reset_index()
                hdbdf.columns=[str(count)+'_character',str(count)+'_pct', str(count)+'_stars']

                hdbdf.loc[-2] = ['Count',len(clusterdf[clusterdf['hdb']==i]),'']
                hdbdf.loc[-1] = ['Placement',round(clusterdf[clusterdf['hdb']==i]['participants.placement'].mean(),2),'']
                hdbdf.loc[-3] = ['PickPct', round(100*len(clusterdf[clusterdf['hdb']==i]) / len(clusterdf),2),'']
                hdbdf.loc[-4] = ['Top4Rate',round(100*len(clusterdf[(clusterdf['participants.placement']<4.5) & (clusterdf['hdb']==i)]) / len(clusterdf[clusterdf['hdb']==i]),2),'']
                hdbdf.loc[-5] = ['WinRate',round(100*len(clusterdf[(clusterdf['participants.placement']==1) & (clusterdf['hdb']==i)]) / len(clusterdf[clusterdf['hdb']==i]),2),'']

                rawitemdf['character']=rawitemdf['participants.units.character_id']+'_'+rawitemdf['name']
                itemdf=rawitemdf[['character','count']]
                itemdf['count']= (100* itemdf['count']/ (clusterdf['hdb']==i).sum()).round()
                #need an empty column in items that will go under unit stars
                #not sure of best way,see: https://stackoverflow.com/questions/16327055/how-to-add-an-empty-column-to-a-dataframe
                itemdf['empty'] = ''
                itemdf.columns = hdbdf.columns
                itemdf.index=itemdf.index+100
                hdbitemdf = pd.concat([hdbdf,itemdf])
                allhdbdf = pd.concat([allhdbdf,hdbitemdf],axis=1)
                #empty string looks nicer in spreadsheet than nan
                allhdbdf = allhdbdf.fillna('')
                count = count + 1
        
        self.allhdbdf = allhdbdf
        return allhdbdf