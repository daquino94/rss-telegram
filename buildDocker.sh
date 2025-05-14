docker build -t rss-telegram . --no-cache && \
docker tag rss-telegram asterix94/rss-telegram:develop && \
docker push asterix94/rss-telegram:develop
