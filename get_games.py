from gevent import monkey
monkey.patch_all(thread=False, select=False)

import configparser
import grequests
import math
import json
import time

config = configparser.ConfigParser()
config.read('config.ini')

regions = config.get('adjustable', 'regions').split(',')

for region in regions:
	mark_game = set()

	ladder = open(config.get('setup', 'ladder_dir') + '/ladder-{}.txt'.format(region), "r", encoding="utf-8").readlines()
	log = open('data/raw-games/log.txt', "w")

	urls = []

	for acc in ladder:
		acc = acc[:-1]
		urls.append('https://tft.iesdev.com/graphql?query=query summonerGames($name: String!, $region: String!, $cursor: String) { summoner(name: $name, region: $region) { id name puuid games(first: 20, after: $cursor) { edges { node { id createdAt length queueId isRanked players } } pageInfo { endCursor hasNextPage } } } } &variables={"name": "'+acc+'","region":"'+region+'"}')

	batches = 20
	urls = [urls[i::batches] for i in range(batches)]

	for i in range(batches):
		rs = (grequests.get(url) for url in urls[i])
		rs_map = grequests.map(rs)
		for response in rs_map:
			data = response.json()["data"]["summoner"]
			if data is not None:
				edges = data["games"]["edges"]
				for game in edges:
					info = game["node"]
					id = info["id"]
					if id not in mark_game:
						mark_game.add(id)
						with open(config.get('setup', 'raw_data_dir') + '/{}/{}.json'.format(region,id), "w") as file:
							file.write(json.dumps(info))
						log.write(id+"\n")

		print(i)
		time.sleep(1)
