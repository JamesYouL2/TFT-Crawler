# TFT-Crawler
Blitz.gg crawler for the auto-chess game Teamfight Tactics. <br/>
The original project is creditted to [dawyi](https://github.com/dawyi/) and can be found [here](https://github.com/dawyi/TFT-Crawler).
I modified his project for future scalability.

## Setup
Open the **config.ini** file. It should look like the following below.
Obtain an API key from [RIOT API](https://developer.riotgames.com/) and update the api_key variable with your API key.

```python
[setup]
api_key = Your API Key

patch_time = 27 aug 2019 18:30:00 GMT+0000

ladder_dir = data/ladder
raw_data_dir = data/raw-games
clean_data_dir = data/clean-games
```
<br/>
I set up the directories for the data to be stored such as:
```
.
├── ...
├── data
│   ├── ladder                  # folder containing the ladder data
│   ├── raw-games               # folder for the raw-games
│       ├── na1                 # folder containing the raw-games for NA
│       ├── euw1                # folder containing the raw-games for EUW
│   └── clean-games             # folder containing the clean data
└── ...
```
<br/>
You must create the directories yourself. If you choose to organize or rename the folders, you must also reflect the changes in the **config.ini** file. However, the **na1** and **euw1** folders must remain in the **raw data folder**, unless you modify the source code. I will continue to improve the organization and scalability, but this is what I've decided for now.

## Usage
Run in this order
```
get_ladder.py
```
```
get_games.py
```
```
clean_data.py
```

