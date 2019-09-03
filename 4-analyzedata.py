import pandas as pd
import numpy as np

df=pd.DataFrame()

for region in ["na", "euw"]:
    tmp=pd.read_csv("clean-games/{}.csv".format(region), encoding="utf-8")
    df=df.append(tmp)

df=df.reset_index()

#Calculate Synergies
champlisttrait = pd.read_csv("champlist-trait.txt",sep='-')
unstack=pd.DataFrame(champlisttrait[['Trait1','Trait2','Trait3']].unstack())
unstack['champno']=unstack[0].index.get_level_values(1)

champtrait=pd.merge(champlisttrait['Champion'],unstack,left_index=True,right_on='champno')[['Champion',0]]
champtrait=champtrait.loc[champtrait[0].notna()]
champtrait=champtrait.rename(columns={0: "Trait"})

#Get number of trait
traitlist = pd.read_csv("Traitlist2.txt",sep='\t')

#Champion Analysis
champ=df.loc[df['isRanked']].apply(np.count_nonzero)
champ.sort_values(ascending=False).iloc[0:30]

top4=df.loc[(df['isRanked']) & (df['standing'] < 4.5)].apply(np.count_nonzero)
top4.sort_values(ascending=False).iloc[0:30]

win=df.loc[(df['isRanked']) & (df['standing'] < 1.5)].apply(np.count_nonzero)
win.sort_values(ascending=False).iloc[0:30]

#Comp Testing
for trait in traitlist['Trait']:
    traitchamp=champtrait.loc[champtrait['Trait']==trait]['Champion']
    df[trait]=df[traitchamp].apply(np.count_nonzero,axis=1)

traitdf=pd.DataFrame()
traitdf[['standing','isRanked']] = df[['standing','isRanked']]

for trait in traitlist['Trait']:
    traitlevel = trait + 'Level'
    traitdf[traitlevel]= np.where(df[trait] >= float(traitlist.loc[traitlist['Trait']==trait]['Level1']),1,0)
    traitdf[traitlevel]= np.where(df[trait] >= float(traitlist.loc[traitlist['Trait']==trait]['Level2']),2,traitdf[traitlevel])
    traitdf[traitlevel]= np.where(df[trait] >= float(traitlist.loc[traitlist['Trait']==trait]['Level3']),3,traitdf[traitlevel])

#Trait Analysis
alltrait=traitdf.loc[traitdf['isRanked']]
top4trait=traitdf.loc[(traitdf['isRanked']) & (traitdf['standing'] < 4.5)]
wintrait=traitdf.loc[(traitdf['isRanked']) & (traitdf['standing'] < 1.5)]

alltrait.apply(np.count_nonzero).sort_values(ascending=False).iloc[0:30]
top4trait.apply(np.count_nonzero).sort_values(ascending=False).iloc[0:30]
wintrait.apply(np.count_nonzero).sort_values(ascending=False).iloc[0:30]

alltrait.apply(pd.Series.value_counts).to_csv('alltraitlevel.csv')
top4trait.apply(pd.Series.value_counts).to_csv('top4traitlevel.csv')
wintrait.apply(pd.Series.value_counts).to_csv('wintraitlevel.csv')

alltrait.groupby(list(traitlist['Trait']+'Level')).size().reset_index(name='Count').sort_values(by='Count',ascending=False).to_csv('alltrait.csv')
top4trait.groupby(list(traitlist['Trait']+'Level')).size().reset_index(name='Count').sort_values(by='Count',ascending=False).to_csv('top4trait.csv')
wintrait.groupby(list(traitlist['Trait']+'Level')).size().reset_index(name='Count').sort_values(by='Count',ascending=False).to_csv('wintrait.csv')

