import pandas as pd
import numpy as np
import pygsheets
import datetime

df=pd.DataFrame()

for region in ["na1", "euw1"]:
    tmp=pd.read_csv("data/clean-games/{}.csv".format(region), encoding="utf-8")
    df=df.append(tmp)

df=df.reset_index()

df=df.loc[df[champlistgold['Champion']].sum(axis=1)>0]

#Calculate Synergies
champlisttrait = pd.read_csv("champlist-trait.txt",sep='-')
champlistgold = pd.read_csv("champlist-gold.txt",sep='\t')
unstack=pd.DataFrame(champlisttrait[['Trait1','Trait2','Trait3']].unstack())
unstack['champno']=unstack[0].index.get_level_values(1)

champtrait=pd.merge(champlisttrait['Champion'],unstack,left_index=True,right_on='champno')[['Champion',0]]
champtrait=champtrait.loc[champtrait[0].notna()]
champtrait=champtrait.rename(columns={0: "Trait"})

#Get number of trait
traitlist = pd.read_csv("Traitlist2.txt",sep='\t')

#Add Traits
for trait in traitlist['Trait']:
    traitchamp=champtrait.loc[champtrait['Trait']==trait]['Champion']
    df[trait]=df[traitchamp].apply(np.count_nonzero,axis=1)

#Add TraitLevel
for trait in traitlist['Trait']:
    traitlevel = trait + 'Level'
    df[traitlevel]= np.where(df[trait] >= float(traitlist.loc[traitlist['Trait']==trait]['Level1']),1,0)
    df[traitlevel]= np.where(df[trait] >= float(traitlist.loc[traitlist['Trait']==trait]['Level2']),2,df[traitlevel])
    df[traitlevel]= np.where(df[trait] >= float(traitlist.loc[traitlist['Trait']==trait]['Level3']),3,df[traitlevel])

#FIX DF FOR WEIGHTINGS
weightedstanding=pd.DataFrame(1/df.groupby('standing').size(),columns=['WeightedStanding'])
weightedstanding=weightedstanding/weightedstanding.sum()
df=df.merge(weightedstanding,left_on='standing',right_on='standing')

standingdf=df.loc[df['isRanked']].groupby('standing').sum().reset_index()
standingdf.index = np.arange(1, len(standingdf) + 1)
origstanding = standingdf['standing']
standingdf=standingdf.multiply(weightedstanding['WeightedStanding'],axis=0)

champtotalstanding=standingdf.mul(origstanding,axis=0).sum()
champsum=standingdf.sum()

avgdf=pd.concat([champtotalstanding,champsum],axis=1)
avgdf.columns = ['TotalStanding','Sum']

avgdf['AverageRank'] = avgdf['TotalStanding'] / avgdf['Sum']

#Champion Analysis
champdf = df[champlistgold['Champion'].append(pd.Series('standing'))]
champ=champdf.loc[df['isRanked']].apply(np.count_nonzero)
top4=champdf.loc[(df['isRanked']) & (df['standing'] < 4.5)].apply(np.count_nonzero)
win=champdf.loc[(df['isRanked']) & (df['standing'] < 1.5)].apply(np.count_nonzero)

#Trait Analysis
traitdf = df[traitlist['Trait'].append(pd.Series('standing'))]
alltrait=traitdf.loc[df['isRanked']].reset_index(drop=True)
top4trait=traitdf.loc[(df['isRanked']) & (df['standing'] < 4.5)].reset_index(drop=True)
wintrait=traitdf.loc[(df['isRanked']) & (df['standing'] < 1.5)].reset_index(drop=True)

#get championsheet
championlist = [champ, top4, win]
championsheet=pd.DataFrame().join(championlist, how="outer")
championsheet.columns = ['All','Top4','Win']
championsheet = championsheet.rename({"standing":"Total"})

championsheet['PercentAll']=100*championsheet['All']/championsheet['All']['Total']
championsheet['PercentTop4']=100*championsheet['Top4']/championsheet['Top4']['Total']
championsheet['PercentWin']=100*championsheet['Win']/championsheet['Win']['Total']

championsheet['Top4AboveExpectation']=championsheet['PercentTop4']-championsheet['PercentAll']
championsheet['WinAboveExpectation']=championsheet['PercentWin']-championsheet['PercentAll']

championsheet=championsheet.join(avgdf['AverageRank'],how="left")
championsheet=championsheet.merge(champlistgold,how="left",left_index=True,right_on='Champion')
championsheet.set_index('Champion',inplace=True)

#GetTraitSheet
traitarray=[alltrait.apply(np.count_nonzero),top4trait.apply(np.count_nonzero),wintrait.apply(np.count_nonzero)]
traitsheet=pd.DataFrame().join(traitarray, how="outer")
traitsheet.columns = ['All','Top4','Win']
traitsheet = traitsheet.rename({"standing":"Total"})

traitsheet=traitsheet.join(avgdf['AverageRank'],how="left")

#GetTraitLevelSheet
traitlevellist = pd.Series(traitlist['Trait']+'Level')

traitleveldf = df[traitlevellist.append(pd.Series('standing'))]

alllevel=traitleveldf.loc[df['isRanked']].reset_index(drop=True)
top4level=traitleveldf.loc[(df['isRanked']) & (df['standing'] < 4.5)].reset_index(drop=True)
winlevel=traitleveldf.loc[(df['isRanked']) & (df['standing'] < 1.5)].reset_index(drop=True)

levelarray=[alllevel,top4level,winlevel]
tmplevelsheet=alllevel.merge(top4level, left_on=traitlevellist, right_on=traitlevellist, how='outer')
levelsheet=tmplevelsheet.merge(winlevel, left_on=traitlevellist, right_on=traitlevellist, how='left')
levelsheet=levelsheet.fillna(0)
levelsheet=levelsheet.merge(avgdf,left_on=traitlevellist, right_on=traitlevellist)
levelsheet=levelsheet.rename(columns={0: "AverageRank"})

allmelt = alltrait.melt().groupby(['variable', 'value']).size()
top4melt = top4trait.melt().groupby(['variable', 'value']).size()
winmelt = wintrait.melt().groupby(['variable', 'value']).size()

avgmelt=alltrait.melt(id_vars='standing').groupby(['standing','variable', 'value']).size().reset_index()
avgmelt['totalstanding']=avgmelt['standing']*avgmelt[0]
avgmeltarray=avgmelt.groupby(['variable','value']).sum().reset_index()
avgmeltarray['value']=avgmeltarray['value'].apply(int)
avgmeltarray['AverageRank']=avgmeltarray['totalstanding']/avgmeltarray[0]

meltarray=[allmelt,top4melt,winmelt]
tmpmeltsheet=pd.DataFrame().join(meltarray, how='outer')
tmpmeltsheet.reset_index(inplace=True)
tmpmeltsheet.columns = ['TraitLevel','All','Top4','Win']
meltcolumns=tmpmeltsheet['TraitLevel'].apply(pd.Series)
meltsheet=meltcolumns.join(tmpmeltsheet,how='left')
meltsheet.columns = ['Trait','Level','Tuple','All','Top4','Win']
meltsheet=meltsheet[meltsheet['Trait'].str.contains('Level')]
meltsheet=meltsheet.drop(columns='Tuple')
meltsheet=meltsheet.fillna(0)
meltsheet=meltsheet.merge(avgmeltarray[['AverageRank', 'variable', 'value']],left_on=['Trait','Level'],right_on=['variable','value'])
meltsheet=meltsheet.drop(columns=['variable','value'])

#alltrait.apply(pd.Series.value_counts)
#top4trait.apply(pd.Series.value_counts)
#wintrait.apply(pd.Series.value_counts)

#Google Spreadsheet
gc = pygsheets.authorize(service_file='./Test.json')

#open the google spreadsheet (where 'PY to Gsheet Test' is the name of my sheet)
sh = gc.open('TFTSheet')

#Set Spreadsheet to df
wks = sh[0]
wks.set_dataframe(championsheet.round(1).sort_values('All',ascending=False),(1,1),copy_index=True)

wks1 = sh[1]
wks1.set_dataframe(traitsheet.round(2).sort_values('All',ascending=False),(1,1),copy_index=True)

wks2 = sh[2]
wks2.set_dataframe(levelsheet.round(2).sort_values('All',ascending=False),(1,1))

wks3 = sh[3]
wks3.set_dataframe(meltsheet.round(2),(1,1))

wks4 = sh[4]
header = wks4.cell('A1')
header.value = 'Date Updated: ' + str(datetime.datetime.now()) 
header.set_text_format('bold', True)
header.update()