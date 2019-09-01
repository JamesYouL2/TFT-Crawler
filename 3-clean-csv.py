import pandas as pd
import os
import json
from dateutil import parser
patch_time = parser.parse("27 aug 2019 18:30:00 GMT+0000")   

champ_list = open("E:/project/TFT/data/ChampList-order.txt").readlines()
champ_list = list(map(lambda x: x[:-1], champ_list))

loger = open("log.txt", "w", encoding="utf-8")
for region in ["na", "euw"]:
	all = []
	log=0
	for name in os.listdir("E:/project/TFT/data/raw-games/2-sep/1-sep/{}".format(region)):
		with open("E:/project/TFT/data/raw-games/2-sep/1-sep/{}/{}".format(region, name), 'r', encoding="utf-8") as file:
			print(log)
			log += 1
			loger.write(name+"\n")
			js = json.loads(file.read())
			created_at = parser.parse(js["createdAt"][:-29])
			if created_at < patch_time:
				continue
			isRanked = js["isRanked"]
			for player in js["players"]:
				sname = player["summonerName"]
				standing = player["ffaStanding"]
				if standing == 0:
					continue
				row = dict((c, 0) for c in champ_list)
				for champ in player["boardPieces"]:
					if champ["name"] in champ_list:
						row[champ["name"]] = champ["level"]
				win = 1 if standing < 5 else 0
				row["summonerName"] = sname
				row["isRanked"] = isRanked
				row["win"] = win
				row["id"] = name[:-5]
				row["standing"] = standing
				all.append(row)
	pd.DataFrame(all).to_csv("E:/project/TFT/data/clean-games/2-sep/1-sep/{}.csv".format(region), encoding="utf-8")
