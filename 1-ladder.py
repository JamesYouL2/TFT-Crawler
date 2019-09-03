import requests
from bs4 import BeautifulSoup 
import time

for region in ["euw", "na", "kr"]:
	file = open("ladder-{}.txt".format(region), "w", encoding="utf-8")
	for i in range(1,10):
		print(i)
		req = requests.get("https://lolchess.gg/leaderboards?region={}&page=".format(region)+str(i))
		bs = BeautifulSoup(req.text)
		if i == 1:
			table = bs.find('table', attrs={'class':'table-page-1'})
		else:
			table = bs.find('table', attrs={'class':'table-page-0'})
		rows = table.find_all("a")
		for row in rows:
			name = row.get_text().strip()
			file.write(name+"\n")
		time.sleep(1)
