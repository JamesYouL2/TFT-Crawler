import hdbscan
import numpy as np
import seaborn as sns
clusterdf = df

hdb = hdbscan.HDBSCAN(min_cluster_size=int(np.floor(len(clusterdf)/40)), min_samples=int(np.floor(len(clusterdf)/500)))
columns = ['Camille', 'Darius', 'Elise', 'Fiora', 'Garen',
'Graves', 'Kassadin', "Kha'Zix", 'Mordekaiser', 'Nidalee', 'Tristana',
'Vayne', 'Warwick', 'Ahri', 'Blitzcrank', 'Braum', 'Jayce', 'Lissandra',
'Lucian', 'Lulu', 'Pyke', "Rek'Sai", 'Shen', 'Twisted Fate', 'Varus',
'Zed', 'Aatrox', 'Ashe', 'Evelynn', 'Gangplank', 'Katarina', 'Kennen',
'Morgana', 'Poppy', 'Rengar', 'Shyvana', 'Veigar', 'Vi', 'Volibear',
'Akali', 'Aurelion Sol', 'Brand', "Cho'Gath", 'Draven', 'Gnar', 'Jinx',
'Kindred', 'Leona', 'Sejuani', 'Anivia', 'Karthus', 'Kayle',
'Miss Fortune', 'Pantheon', 'Swain', 'Yasuo', 'Assassin', 'Blademaster',
'Brawler', 'Demon', 'Dragon', 'Elementalist', 'Exile', 'Glacial',
'Guardian', 'Gunslinger', 'Hextech', 'Imperial', 'Knight', 'Ninja',
'Noble', 'Phantom', 'Pirate', 'Ranger', 'Robot', 'Shapeshifter',
'Sorcerer', 'Void', 'Wild', 'Yordle']

clusterer=hdb.fit(clusterdf[columns])

clusterdf['hdb'] = pd.Series(hdb.labels_+1, index=clusterdf.index)
clusterdf['hdb'].value_counts()

trait = ['Assassin', 'Blademaster',
'Brawler', 'Demon', 'Dragon', 'Elementalist', 'Exile', 'Glacial',
'Guardian', 'Gunslinger', 'Hextech', 'Imperial', 'Knight', 'Ninja',
'Noble', 'Phantom', 'Pirate', 'Ranger', 'Robot', 'Shapeshifter',
'Sorcerer', 'Void', 'Wild', 'Yordle']

clusterdf.groupby('hdb')[trait].mean().idxmax(axis=1)

clusterdf.groupby('hdb')[trait].mean()
clusterdf.groupby('hdb')['standing'].mean()

plot = clusterer.condensed_tree_.plot(select_clusters=True,
                               selection_palette=sns.color_palette('deep', 8))