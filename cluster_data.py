import hdbscan
import numpy as np
import seaborn as sns
import pandas as pd
import pygsheets

clusterdf = df
clusterdf['TotalWeightedStanding']=clusterdf['WeightedStanding']*clusterdf['standing']

hdb = hdbscan.HDBSCAN(min_cluster_size=
int(np.floor(len(clusterdf)/15)), 
min_samples=1,
cluster_selection_method='leaf')
hdb2 = hdbscan.HDBSCAN(min_cluster_size=
int(np.floor(len(clusterdf)/20)), 
min_samples=1,
cluster_selection_method='leaf')

columns = ['Camille', 'Darius', 'Elise', 'Fiora', 'Garen',
'Graves', 'Kassadin', "Kha'Zix", 'Mordekaiser', 'Nidalee', 'Tristana',
'Vayne', 'Warwick', 'Ahri', 'Blitzcrank', 'Braum', 'Jayce', 'Lissandra',
'Lucian', 'Lulu', 'Pyke', "Rek'Sai", 'Shen', 'Twisted Fate', 'Varus',
'Zed', 'Aatrox', 'Ashe', 'Evelynn', 'Gangplank', 'Katarina', 'Kennen',
'Morgana', 'Poppy', 'Rengar', 'Shyvana', 'Veigar', 'Vi', 'Volibear',
'Akali', 'Aurelion Sol', 'Brand', "Cho'Gath", 'Draven', 'Gnar', 'Jinx',
'Kindred', 'Leona', 'Sejuani', 'Anivia', 'Karthus', 'Kayle',
'Miss Fortune', 'Pantheon', 'Swain', 'Yasuo', "Kai'Sa", 'Assassin', 'Blademaster',
'Brawler', 'Demon', 'Dragon', 'Elementalist', 'Exile', 'Glacial',
'Guardian', 'Gunslinger', 'Hextech', 'Imperial', 'Knight', 'Ninja',
'Noble', 'Phantom', 'Pirate', 'Ranger', 'Robot', 'Shapeshifter',
'Sorcerer', 'Void', 'Wild', 'Yordle',
'AssassinLevel', 'BlademasterLevel', 'BrawlerLevel', 'DemonLevel',
'DragonLevel', 'ElementalistLevel', 'ExileLevel', 'GlacialLevel',
'GuardianLevel', 'GunslingerLevel', 'HextechLevel', 'ImperialLevel',
'KnightLevel', 'NinjaLevel', 'NobleLevel', 'PhantomLevel',
'PirateLevel', 'RangerLevel', 'RobotLevel', 'ShapeshifterLevel',
'SorcererLevel', 'VoidLevel', 'WildLevel', 'YordleLevel']

clusterer=hdb.fit(clusterdf[columns])
clusterdf['hdb'] = pd.Series(hdb.labels_+1, index=clusterdf.index)
print(clusterdf['hdb'].value_counts())
plot = clusterer.condensed_tree_.plot(select_clusters=True,
                               selection_palette=sns.color_palette('deep', 8))

clusterer2=hdb2.fit(clusterdf[columns])
clusterdf['hdb2'] = pd.Series(hdb2.labels_+1, index=clusterdf.index)
print(clusterdf['hdb2'].value_counts())


with pd.option_context('display.max_rows', None, 'display.max_columns', None):
    print(clusterdf.groupby('hdb')['hdb2'].value_counts())
    print(clusterdf['hdb'].value_counts().sort_index())
    print(clusterdf['hdb2'].value_counts().sort_index())
    print(sum(clusterdf['hdb']==0),sum(clusterdf['hdb2']==0))

plot2 = clusterer2.condensed_tree_.plot(select_clusters=True,
                               selection_palette=sns.color_palette('deep', 8))

trait = ['Assassin', 'Blademaster',
'Brawler', 'Demon', 'Dragon', 'Elementalist', 'Exile', 'Glacial',
'Guardian', 'Gunslinger', 'Hextech', 'Imperial', 'Knight', 'Ninja',
'Noble', 'Phantom', 'Pirate', 'Ranger', 'Robot', 'Shapeshifter',
'Sorcerer', 'Void', 'Wild', 'Yordle']

champion = ['Camille', 'Darius', 'Elise', 'Fiora', 'Garen',
'Graves', 'Kassadin', "Kha'Zix", 'Mordekaiser', 'Nidalee', 'Tristana',
'Vayne', 'Warwick', 'Ahri', 'Blitzcrank', 'Braum', 'Jayce', 'Lissandra',
'Lucian', 'Lulu', 'Pyke', "Rek'Sai", 'Shen', 'Twisted Fate', 'Varus',
'Zed', 'Aatrox', 'Ashe', 'Evelynn', 'Gangplank', 'Katarina', 'Kennen',
'Morgana', 'Poppy', 'Rengar', 'Shyvana', 'Veigar', 'Vi', 'Volibear',
'Akali', 'Aurelion Sol', 'Brand', "Cho'Gath", 'Draven', 'Gnar', 'Jinx',
'Kindred', 'Leona', 'Sejuani', 'Anivia', 'Karthus', 'Kayle',
'Miss Fortune', 'Pantheon', 'Swain', 'Yasuo', "Kai'Sa"]

print(clusterdf.groupby('hdb')[champion].mean().idxmax(axis=1))
print(clusterdf.groupby('hdb')[trait].mean().idxmax(axis=1))
print(clusterdf.groupby('hdb')['TotalWeightedStanding'].sum()/clusterdf.groupby('hdb')['WeightedStanding'].sum())

clusterdf.groupby('hdb')[trait].mean().to_excel('C:/Data/trait.xlsx')

clipdf = clusterdf[champion].clip(upper=1).join(clusterdf['hdb'])

#Google Spreadsheet
gc = pygsheets.authorize(service_file='./Test.json')

#open the google spreadsheet (where 'PY to Gsheet Test' is the name of my sheet)
sh = gc.open('TFTSheet')
wks4 = sh[4]
wks4.clear()

for i in clipdf['hdb'].unique():
    print(i)
    hdbdf=pd.DataFrame(clipdf[champion][clipdf['hdb']==i].mean().sort_values(ascending=False).round(3)*100)
    hdbdf.columns=['Percentage']
    wks4.set_dataframe(hdbdf,(2,i*2+1),copy_index=True,copy_head=False)

wks5 = sh[5]
wks5.clear()
wks5.set_dataframe(pd.DataFrame(clusterdf['hdb'].value_counts().sort_index()),(2,1),copy_index=True,copy_head=False)

pd.DataFrame(clusterdf.groupby('hdb')['TotalWeightedStanding'].sum()/clusterdf.groupby('hdb')['WeightedStanding'].sum())

wks5.set_dataframe(pd.DataFrame(clusterdf.groupby('hdb')['TotalWeightedStanding'].sum()/clusterdf.groupby('hdb')['WeightedStanding'].sum()),(2,3),copy_index=False,copy_head=False)

#Melt for interesting comp
melttemp = clusterdf[clusterdf['hdb']==7][traitlevellist].melt().groupby(['variable', 'value']).size()
with pd.option_context('display.max_rows', None, 'display.max_columns', None):
    display(melttemp)

    
print(clusterdf.groupby('hdb2')[champion].mean().idxmax(axis=1))
print(clusterdf.groupby('hdb2')[trait].mean().idxmax(axis=1))
print(clusterdf.groupby('hdb2')['TotalWeightedStanding'].sum()/clusterdf.groupby('hdb2')['WeightedStanding'].sum())
