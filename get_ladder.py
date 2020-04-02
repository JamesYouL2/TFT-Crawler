import configparser
import requests
import time
from pathlib import Path

def main():
	config = configparser.ConfigParser()
	config.read('config.ini')

	regions = config.get('adjustable', 'regions').split(',')
	leagues = config.get('adjustable', 'leagues').split(',')

	Path(config.get('setup', 'ladder_dir')).mkdir(parents=True, exist_ok=True)
	for region in regions:
		file = open(config.get('setup', 'ladder_dir') + '/ladder-{}.txt'.format(region), "w", encoding="utf-8")
		for league in leagues:
			url = config.get('default', 'ladder_url').format(region, league, config.get('setup', 'api_key'))
			print(url)
			try:
				response = requests.get(url)
				response.raise_for_status()
				if (response.status_code == 200):
					entries = response.json()['entries']
					players = [file.write(entry['summonerName'] + '\n') for entry in entries]
			except:
				print("something failed")
			time.sleep(.1)
