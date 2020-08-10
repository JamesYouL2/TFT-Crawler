#1. Build Dockerfile
docker build . -f Dockerfile -t tft-crawler
#2. Docker Run
docker run --dns 8.8.8.8 --rm -it -v ${PWD}:/app tft-crawler 
