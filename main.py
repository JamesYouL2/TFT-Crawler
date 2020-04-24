import loadpuuid
import loadmatchhistory
import asyncio

#new Workflow
print ("Get puuid")
asyncio.run(loadpuuid.main())

print ("Get matchhistory")
asyncio.run(loadmatchhistory.main())