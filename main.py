#import loadpuuid
#import loadmatchhistory
import save_matchdata
import asyncio
import time

#new Workflow
start=time.time()
print ("Create Clusters")
save_matchdata.main(hours=24, divisor = 50, 
unitsscalar = 0.5, traitsscalar = 1.5,
chosentraitscalar = 1.5, chosenunitsscalar=1.0, traitsnumunitscalar=1.0)
print("GetClusterTime:",(time.time()-start)/60)