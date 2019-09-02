from gevent import monkey as curious_george
curious_george.patch_all(thread=False, select=False)
import requests
import grequests
import json
import time

for region in ["euw","na","kr"]:
	mark_game = set()

	ladder = open("ladder-{}.txt".format(region), "r", encoding="utf-8").readlines()
	log = open('log.txt', "w")

	urls = []

	for acc in ladder:
		acc = acc[:-1]
		urls.append('https://tft.iesdev.com/graphql?query=query summonerGames($name: String!, $region: String!, $cursor: String) { summoner(name: $name, region: $region) { id name puuid games(first: 20, after: $cursor) { edges { node { id createdAt length queueId isRanked players } } pageInfo { endCursor hasNextPage } } } } &variables={"name": "'+acc+'","region":"'+region+'1"}')
	for i in range(20):
		rs = (grequests.get(url) for url in urls[i*50:(i+1)*50])
		x = grequests.map(rs)
		for req in x:
			data = json.loads(req.text)["data"]["summoner"]
			if data is not None:
				games = data["games"]["edges"]
				for game in games:
					info = game["node"]
					id = info["id"]
					if id not in mark_game:
						mark_game.add(id)
						with open('raw-games/{}/{}.json'.format(region,id), "w") as file:
							file.write(json.dumps(info))
						log.write(id+"\n")
		time.sleep(1)
		print(i)