import configparser
import json
import os
import pandas as pd
import requests

from dateutil import parser

config = configparser.ConfigParser()
config.read('config.ini')

patch_time = parser.parse(config.get('setup', 'patch_time'))

#response = requests.get(config.get('default', 'champions_url'))
#champion_dict = response.json()
#champ_list = list(champion_dict.keys())

champ_list = open("ChampList-order.txt").readlines()
champ_list = list(map(lambda x: x[:-1], champ_list))

regions = config.get('adjustable', 'regions').split(',')

logger = open("log.txt", "w", encoding="utf-8")
for region in regions:
	all = []
	log=0
	for name in os.listdir(config.get('setup', 'raw_data_dir') + '/{}'.format(region)):
		with open(config.get('setup', 'raw_data_dir') + '/{}/{}'.format(region, name), 'r', encoding="utf-8") as file:
			print(log)
			log += 1
			logger.write(name+"\n")
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

	pd.DataFrame(all).to_csv(config.get('setup', 'clean_data_dir') + '/{}.csv'.format(region), encoding="utf-8")
