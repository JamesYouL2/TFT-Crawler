import loadpuuid
import loadmatchhistory
import save_matchdata
import asyncio

#new Workflow
print ("Get puuid")
asyncio.run(loadpuuid.main())

print ("Get matchhistory")
asyncio.run(loadmatchhistory.main())

print ("Create Clusters")
save_matchdata.main()