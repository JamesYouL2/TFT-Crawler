﻿#1. Build Dockerfile
docker build . -f .devcontainer\Dockerfile -t tft-crawler
#2. Docker Push
docker push tft-crawler jamesyou12/tft-crawler
#3. Docker Run
docker run --rm -it -v ${PWD}:/app jamesyou12/tft-crawler