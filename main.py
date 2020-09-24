#import loadpuuid
#import loadmatchhistory
import save_matchdata
import asyncio
import time

#new Workflow
start=time.time()
print ("Create Clusters")
save_matchdata.main(hours=24*7, divisor = 50)
print("GetClusterTime:",(time.time()-start)/60)
