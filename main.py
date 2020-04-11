import get_ladder

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

#export tier list
print ("Create Tier List")
exec(open('save_matchdata.py').read())
