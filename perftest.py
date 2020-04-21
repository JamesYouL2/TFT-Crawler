from loadpuuid import getnameswithoutpuuid
import configparser
from pantheon import pantheon

config = configparser.ConfigParser()
config.read('config.ini')

key = configparser.ConfigParser()
key.read('keys.ini')

#requestslog
def requestsLog(url, status, headers):
    print(url)
    print(status)
    print(headers)


region = "euw1"
panth = pantheon.Pantheon(region, key.get('setup', 'api_key'), errorHandling=True, requestsLoggingFunction=requestsLog, debug=True)

summonernames = getnameswithoutpuuid(region, panth)