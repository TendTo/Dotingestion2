#!/bin/bash

until curl -X PUT "http://elasticsearch:9200/matches/" -H 'Content-Type: application/json' -d'
    {
        "mappings": {
            "properties": {
                "location": {
                    "type": "geo_point"
                }
            }
        }
    }'; do
  echo "curl: Elasticsearch is unavailable - retry later"
  sleep 10
done

curl -X PUT "http://elasticsearch:9200/matches/_mapping" -H 'Content-Type: application/json' -d'
    {
        "properties": {
            "location": {
                "type": "geo_point"
            }
        }
    }'

exec /bin/connect-standalone /etc/kafka/connect-standalone.properties /etc/kafka/elasticsearch-sink.properties