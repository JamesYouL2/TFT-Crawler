#1. check out updatedocs branch
git checkout updatedocs -q
#2. Build Dockerfile
docker build . -f Dockerfile -t tft-crawler
#3. Docker Run
docker run --rm -it -v ${PWD}:/app tft-crawler
#4. Update Tier List
git commit -a -m "Update tierlist.md"
#5. Git Push
git push -q