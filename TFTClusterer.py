import json
import pandas as pd
import hdbscan
import numpy as np
import umap
import seaborn as sns
from matplotlib import pyplot as plt
import re
from sklearn.preprocessing import normalize, scale
from sklearn.decomposition import PCA

class TFTClusterer:
    def __init__(self, df, traitsscalar = 1, unitsscalar = 1, traitsnumunitscalar = 1, 
    chosenunitscalar = 1, chosentraitscalar = 1):
        allrecords = df.to_json(orient='records')

        traits = pd.json_normalize(json.loads(allrecords), 
        record_path=['participants','traits'],
        meta=['match_id',['participants','placement'],['participants','puuid']])

        units = pd.json_normalize(json.loads(allrecords), 
        record_path=['participants','units'],
        meta=['match_id',['participants','placement'],['participants','puuid'],['participants','level']])

        items = pd.json_normalize(json.loads(allrecords),
        record_path=['participants','units', 'items'],
        meta=['match_id',['participants','placement'],['participants','puuid'],['participants','units','character_id']])

        units['gold'] = units['rarity'] + 1

        items.rename(columns={0: "item"},inplace=True)
        items['count']=1
        items=items.merge(pd.read_json('items.json'),left_on='item',right_on='id')

        traits=traits.merge(pd.read_json('traits.json'),left_on='name',right_on='key')
        traits['name']=traits['name_y']
        minunits = pd.DataFrame(traits.groupby(['name','tier_current']).num_units.min())
        minunits.columns=['minunit']
        traits = pd.merge(minunits,traits,left_index=True,right_on=['name','tier_current'])

        self.itemsdf = items
        self.unitsdf = units
        self.traitsdf = traits
        
        #Pivot and combine spreadsheets
        unitspivot=pd.pivot_table(units,index=['match_id','participants.placement'], columns='character_id',values='tier')
        traitspivot=pd.pivot_table(traits,index=['match_id','participants.placement'], columns='name',values='minunit')
        traitsnumunitpivot=pd.pivot_table(traits,index=['match_id','participants.placement'], columns='name',values='num_units')
        #itemspivot=pd.pivot_table(items,index=['match_id','participants.placement'], columns=['participants.units.character_id'],values='count',aggfunc=np.sum)
        chosenunitpivot=pd.pivot_table(units,index=['match_id','participants.placement'], columns='character_id',values='chosen',aggfunc='first')
        chosenunitpivot=chosenunitpivot.notnull().astype('int')
        chosentraitpivot=pd.pivot_table(units,index=['match_id','participants.placement'], columns='chosen',values='tier')
        chosentraitpivot = chosentraitpivot.notnull().astype('int')

        unitspivot = unitspivot * unitsscalar
        traitspivot = traitspivot * traitsscalar
        traitsnumunitpivot = traitsnumunitpivot * traitsnumunitscalar
        chosenunitpivot = chosenunitpivot * chosenunitscalar
        chosentraitpivot = chosentraitpivot * chosentraitscalar

        traitsnumunitpivot.columns = traitsnumunitpivot.columns + 'numunit'
        chosentraitpivot.columns = chosentraitpivot.columns + 'chosen'
        chosenunitpivot.columns = chosenunitpivot.columns + 'chosen'

        dfs = [unitspivot, traitspivot, traitsnumunitpivot, chosenunitpivot, chosentraitpivot]

        self.clusterdf = dfs[0].join(dfs[1:]).reset_index()
        #self.clusterdf = self.clusterdf.fillna(0)

        self.unitscol=list(unitspivot.columns)
        self.traitscol=list(traitspivot.columns)
        self.itemscol=list(items.columns)
        self.traitsnumunitcol=list(traitsnumunitpivot.columns)
        self.chosenunitpivotcol = list(chosenunitpivot.columns)
        self.chosentraitpivotcol = list(chosentraitpivot.columns)

        self.unitspivot = unitspivot

    def cluster(self, divisor = 30, cluster_selection_epsilon = 0, metric = 'euclidean', algorithm = 'best', n_components = 10):
        #HDB Scan
        hdb = hdbscan.HDBSCAN(min_cluster_size=
        int(np.floor(len(self.clusterdf) / divisor)), 
        min_samples=1,
        cluster_selection_method='eom'
        ,cluster_selection_epsilon=cluster_selection_epsilon
        ,metric= metric
        ,algorithm=algorithm
        )

        #Normalize data
        cols = self.unitscol + self.traitscol + self.traitsnumunitcol + self.chosenunitpivotcol + self.chosentraitpivotcol
        data = self.clusterdf[cols].fillna(0)
        norm_data = normalize(data, norm='l2')

        ##Cannot make dimension reduction work
        #reducer = umap.UMAP(metric = 'manhattan', random_state = 42, n_components = n_components)
        #embed = reducer.fit_transform(norm_data)

        embed = norm_data

        #print(cols)
        #Cluster HDB
        print('HDB Scan')
        clusterer=hdb.fit(embed)

        try:
            self.plot = clusterer.condensed_tree_.plot(select_clusters=True, label_clusters=True)
        except:
            pass
        
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
        self.unitshdb=self.unitsdf.merge(self.clusterdf[['match_id','participants.placement','comp_id','hdb']])[list(self.unitsdf.columns)+list(['hdb'])+list(['comp_id'])]
        self.itemshdb=self.itemsdf.merge(self.clusterdf)[list(self.itemsdf.columns)+list(['hdb'])+list(['comp_id'])]

        comppop=pd.DataFrame(self.clusterdf.groupby('match_id')['hdb'].value_counts().rename('compsinmatch'))
        self.clusterdf=pd.merge(self.clusterdf,comppop,left_on=['match_id','hdb'],right_index=True)

    def mostcommon(self):
        clusterdf = self.clusterdf
        unitscol = self.unitscol
        commoncomps = pd.DataFrame()
        for i in clusterdf['hdbnumber'].unique():
            #replace na with 0 to use size
            mostcommondf=clusterdf[clusterdf['hdbnumber']==i]
            mostcommondf.fillna(0,inplace=True)
            countdf=mostcommondf.groupby(unitscol).size().reset_index(name='Count')
            
            #Create list of common comps
            commoncompsdf = pd.DataFrame(countdf.sort_values('Count',ascending=False).head(10).stack(),columns=['Stars'])
            commoncompsdf = commoncompsdf[commoncompsdf['Stars']!=0].reset_index(level=1)
            commoncompsdf.rename(columns={'level_1': 'character_id'}, inplace=True)
            commoncompsdf['Count']=countdf['Count']
            commoncompsdf= commoncompsdf[commoncompsdf['character_id'] != 'Count']

            #get most common 8 unit comps
            common8unitcomps = commoncompsdf[commoncompsdf.groupby(level=0).count()['Stars']==8]
            common8unitcomps = common8unitcomps[common8unitcomps['Count']==common8unitcomps['Count'].max()]
            common8unitcomps['hdbnumber'] = i
            common8unitcomps['nounits'] = 8

            #get most common 8 unit comps
            common9unitcomps = commoncompsdf[commoncompsdf.groupby(level=0).count()['Stars']==9]
            common9unitcomps = common9unitcomps[common9unitcomps['Count']==common9unitcomps['Count'].max()]
            common9unitcomps['hdbnumber'] = i
            common9unitcomps['nounits'] = 9

            commoncomps=pd.concat([commoncomps,common8unitcomps,common9unitcomps])
        self.commoncomps = commoncomps

    def allhdbdfcreate(self):
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

    def imputetraits(self):
        championsjson = pd.read_json('champions.json')
        championsjson = championsjson.explode('traits')
        
        traitsdf=self.unitsdf.merge(championsjson,left_on='character_id',right_on='championId')
        traitsdf=pd.melt(traitsdf,id_vars=['match_id','participants.placement'],value_vars='traits')
        traitsdf=pd.DataFrame(traitsdf.groupby(['match_id','participants.placement'])['value'].value_counts())
        traitsdf.columns=['number']
        traitsdf=traitsdf.reset_index()
        
        traitsjson = pd.read_json('traits.json')
        traitsjson = traitsjson.explode('sets').reset_index()
        traitsjson = traitsjson.join(traitsjson['sets'].apply(pd.Series))
        traitsjson['max']=traitsjson['max'].fillna(100).apply(int)

        traitsmerge=traitsdf.merge(traitsjson,left_on='value',right_on='name')
        traitsmerge=traitsmerge[traitsmerge['number']>=traitsmerge['min']]
        traitsmerge=traitsmerge[traitsmerge['number']<=traitsmerge['max']]

        self.traitspivot=pd.pivot_table(traitsmerge,index=['match_id','participants.placement'],columns='name',values='min')
        
        self.clusterdf = self.unitspivot.join(self.traitspivot).reset_index()

    # reduce dimensions
    def reduce_dimension_graph(self, n_components = 2):
        cols = self.unitscol + self.traitscol
        reducer = umap.UMAP(metric = 'manhattan', random_state = 42, n_components = n_components)
        clusterdf = self.clusterdf.fillna(0)
        embed = reducer.fit_transform(clusterdf[cols])
        self.clusterdf['embed_x'], self.clusterdf['embed_y'] = embed[:,0], embed[:,1]

    # plot
    def visualize(self, colors):
        plt.figure(num=None, figsize=(6, 4), dpi=80, facecolor='w', edgecolor='k')
        scat = plt.scatter(
            self.clusterdf['embed_x'],
            self.clusterdf['embed_y'],
            c = colors)
        plt.legend(
            *scat.legend_elements(),
            loc="lower left",)
        plt.savefig('nmap.png')
        self.nmapplt = plt
        plt.show()

    # assign color to clusterdf
    def make_cluster_colors(self):
        color_palette = sns.color_palette(
            'deep', self.clusterdf['hdbnumber'].nunique())
        cluster_colors = [
            color_palette[x]
            if x >= 1
            else (0.5, 0.5, 0.5)
            for x in self.clusterdf['hdbnumber']]
        return cluster_colors

    # evaluate clustering
    def eval_clustering(self):
        self.visualize(self.make_cluster_colors())

    # reduce dimensions
    def reduce_dimension(self, n_components = 2):
        cols = self.unitscol + self.traitscol
        reducer = umap.UMAP(metric = 'manhattan', random_state = 42, n_components = n_components)
        clusterdfcopy = self.clusterdf.fillna(0)
        embed = reducer.fit_transform(clusterdfcopy[cols])
        x = 0
        for i in range(n_components):
            self.clusterdf['clusterembed_' + str(x)] = embed[:,x]
            x = x + 1