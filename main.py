import loadpuuid
import loadmatchhistory
import save_matchdata
import asyncio
import time

#new Workflow
start=time.time()
print ("Get puuid")
asyncio.run(loadpuuid.main())
print("GetpuuidTime:",(time.time()-start)/60)

start=time.time()
print ("Get matchhistory")
asyncio.run(loadmatchhistory.main())
print("GetMatchHistoryTime:",(time.time()-start)/60)

start=time.time()
print ("Create Clusters")
save_matchdata.main()
print("GetClusterTime:",(time.time()-start)/60)
