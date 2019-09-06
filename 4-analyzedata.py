import pandas as pd
import numpy as np
import pygsheets

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
top4=df.loc[(df['isRanked']) & (df['standing'] < 4.5)].apply(np.count_nonzero)
win=df.loc[(df['isRanked']) & (df['standing'] < 1.5)].apply(np.count_nonzero)

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
alltrait=traitdf.loc[traitdf['isRanked']].reset_index(drop=True)
top4trait=traitdf.loc[(traitdf['isRanked']) & (traitdf['standing'] < 4.5)].reset_index(drop=True)
wintrait=traitdf.loc[(traitdf['isRanked']) & (traitdf['standing'] < 1.5)].reset_index(drop=True)

#get championsheet
championlist = [champ, top4, win]
championsheet=pd.DataFrame().join(championlist, how="outer")
championsheet.columns = ['All','Top4','Win']
championsheet = championsheet.drop(['index','Unnamed: 0','summonerName','isRanked','win','id'])
championsheet = championsheet.rename({"standing":"Total"})

traitarray=[alltrait.apply(np.count_nonzero),top4trait.apply(np.count_nonzero),wintrait.apply(np.count_nonzero)]
traitsheet=pd.DataFrame().join(traitarray, how="outer")
traitsheet.columns = ['All','Top4','Win']
traitsheet = traitsheet.drop(['isRanked'])
traitsheet = traitsheet.rename({"standing":"Total"})

allmelt = alltrait.melt().groupby(['variable', 'value']).size()
top4melt = top4trait.melt().groupby(['variable', 'value']).size()
winmelt = wintrait.melt().groupby(['variable', 'value']).size()

meltarray=[allmelt,top4melt,winmelt]
tmpmeltsheet=pd.DataFrame().join(meltarray, how='outer')
tmpmeltsheet.reset_index(inplace=True)
tmpmeltsheet.columns = ['TraitLevel','All','Top4','Win']
meltcolumns=tmpmeltsheet['TraitLevel'].apply(pd.Series)
meltsheet=meltcolumns.join(tmpmeltsheet,how='left')
meltsheet.columns = ['Trait','Level','Tuple','All','Top4','Win']
meltsheet=meltsheet[meltsheet['Trait'].str.contains('Level')]
meltsheet=meltsheet.drop(columns='Tuple')

#alltrait.apply(pd.Series.value_counts)
#top4trait.apply(pd.Series.value_counts)
#wintrait.apply(pd.Series.value_counts)

traitlevellist = list(traitlist['Trait']+'Level')

alllevel=alltrait.groupby(list(traitlist['Trait']+'Level')).size().reset_index(name='All')
top4level=top4trait.groupby(list(traitlist['Trait']+'Level')).size().reset_index(name='Top4')
winlevel=wintrait.groupby(list(traitlist['Trait']+'Level')).size().reset_index(name='Win')

levelarray=[alllevel,top4level,winlevel]
tmplevelsheet=alllevel.merge(top4level, left_on=traitlevellist, right_on=traitlevellist, how='left')
levelsheet=tmplevelsheet.merge(winlevel, left_on=traitlevellist, right_on=traitlevellist, how='left')
levelsheet=levelsheet.fillna(0)

#Google Spreadsheet
gc = pygsheets.authorize(service_file='./Test.json')

#open the google spreadsheet (where 'PY to Gsheet Test' is the name of my sheet)
sh = gc.open('TFTSheet')

#Set Spreadsheet to df
wks = sh[0]
wks.set_dataframe(championsheet,(1,1),copy_index=True)

wks1 = sh[1]
wks1.set_dataframe(traitsheet,(1,1),copy_index=True)

wks2 = sh[2]
wks2.set_dataframe(levelsheet,(1,1))

wks2 = sh[3]
wks3.set_dataframe(levelsheet,(1,1))
