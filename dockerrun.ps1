#1. Build Dockerfile
docker build . -f Dockerfile -t tft-crawler
#2. Docker Run
docker run --rm -it -v ${PWD}:/app tft-crawler 
