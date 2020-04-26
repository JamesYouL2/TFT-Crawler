#TFTSheets

TFTSheets is a project built to display a TFT tier list in a google spreadsheet based master+ games on the most recent patch.

The original project is credited to [dawyi](https://github.com/dawyi/) and can be found [here](https://github.com/dawyi/TFT-Crawler).

It used to crawl blitz before Riot released their own API.

## Setup
Open the **keytemplate.ini** file. It should look like the following below:

```
[setup]
; INPUT YOUR OWN API KEY FROM https://developer.riotgames.com/
api_key = RG_API

[database]
host = 
user = 
password = 
database =
```

Obtain an API key from [Riot API](https://developer.riotgames.com/) and update the api_key variable with your API key.

Also, I'm storing all the data in a postgres database on AWS. Instructions found [here](https://aws.amazon.com/getting-started/tutorials/create-connect-postgresql-db/) to create a postgres db on aws and link it.
Of course, you can also create a local postgres database.

Rename the keytemplate.ini file to keys.ini. 

To apply the spreadsheet to google, you need to create a json file called secrets.json so that pygsheets can use it.

## Usage
main.py calls the other 3 scripts, but there are going to be quite a few libraries that you'll need to install. The dockerfile will list them assuming you have an anaconda install.

Docker Instructions:
Also can run Dockerrun.ps1 if you have a docker desktop (using linux container).