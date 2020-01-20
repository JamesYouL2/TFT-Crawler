import hdbscan
import numpy as np
import seaborn as sns
import pandas as pd
from hyperopt import fmin, tpe, hp, STATUS_OK, Trials

clusterdf = df
clusterdf['TotalWeightedStanding']=clusterdf['WeightedStanding']*clusterdf['standing']

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

def objective(space):
    x=int(space['x'])
    y=int(space['y'])
    hdb = hdbscan.HDBSCAN(min_cluster_size=x, 
    min_samples=y,
    cluster_selection_method='eom')
    hdb.fit(clusterdf[columns])
    val=sum(hdb.labels_==-1)
    return val

space = {
    'x':  hp.quniform('x', 1000, 10000, 1),
    'y': 1
}

trials = Trials()
# Run 2000 evals with the tpe algorithm
tpe_best = fmin(fn=objective, space=space, 
                algo=tpe.suggest, trials=trials, 
                max_evals=10)

print(tpe_best)

hdb = hdbscan.HDBSCAN(min_cluster_size=237, 
min_samples=1, cluster_selection_method='eom')

clusterer=hdb.fit(clusterdf[columns])
clusterdf['hdb'] = pd.Series(hdb.labels_+1, index=clusterdf.index)
plot = clusterer.condensed_tree_.plot(select_clusters=True,
                               selection_palette=sns.color_palette('deep', 8))

print(clusterdf['hdb'].value_counts())