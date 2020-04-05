import get_ladder
#import get_games
#import clean_data

#print ("Get Ladder")
#get_ladder.main()

#print ("Get Games")
#get_games.main()

#print ("Clean Data")
#clean_data.main()

#new Workflow
print ("Get Ladder")
get_ladder.main()

#get_puiid 
print ("Get Puuid")
exec(open('get_puuid.py').read())

#get_matches
print ("Get Match JSON Names")
exec(open('get_matches.py').read())

#get_rawgames
print ("Get Match JSON Files")
exec(open('get_matchdata.py').read())
