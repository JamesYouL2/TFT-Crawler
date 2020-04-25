# TFT-Crawler
TFT API crawler for the auto-chess game Teamfight Tactics.<br/>
The original project is credited to [dawyi](https://github.com/dawyi/) and can be found [here](https://github.com/dawyi/TFT-Crawler).
It used to crawl blitz before Riot released their own API.

## Setup
Open the **keys.ini** file. It should look like the following below:

```python
[setup]
; INPUT YOUR OWN API KEY FROM https://developer.riotgames.com/
api_key = RG_API

Obtain an API key from [Riot API](https://developer.riotgames.com/) and update the api_key variable with your API key.<br/><br/>

Also, I'm storing all the data in a postgres database on AWS. Instructions found [here].(https://aws.amazon.com/getting-started/tutorials/create-connect-postgresql-db/)

[database]
host = 
user = 
password = 
database =

## Usage
Run the programs in this order:
```
main.py (calls the other 3 scripts)
```
Docker Instructions:
Also can run Dockerrun.ps1 (pushes tierlist update to git repo as updatedocs branch) if you have a docker desktop set up under linux.
or 
#1. Build Dockerfile
docker build . -t tft-crawler
#2. Docker Run
docker run --rm -it -v ${PWD}:/app tft-crawler
in bash/git.