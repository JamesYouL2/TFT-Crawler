import pandas as pd

df=pd.DataFrame()

for region in ["na", "euw"]:
    tmp=pd.read_csv("clean-games/{}.csv".format(region), encoding="utf-8")
    df=df.append(tmp)

##Calculate Synergies
champlisttrait = 