#1. Build Dockerfile
#docker build . -f .devcontainer\Dockerfile -t tft-crawler
#2. Docker Push
#docker push tft-crawler jamesyou12/tft-crawler
#3. Docker Run
#docker run --rm -it -v ${PWD}:/app jamesyou12/tft-crawler

#1. Build Dockerfile
docker build . -t tft-crawler
#3. Docker Run
docker run --rm -it -v ${PWD}:/app tft-crawler
#4. Update Tier List
git commit -a -m "Update tierlist.md"
#5. Git Push
git push