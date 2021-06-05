# Dotingestion 2: there is no Dotingestion 1

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/TendTo/Dotingestion2/docs?filepath=Dotingestion2.ipynb)

## Project structure
```py
.
├── api                     # Rest API associated with the data (ExpressJS)
├── cassandra               # Cassandra Dockerfile and init script (Cassandra)
├── connect-cassandra       # Kafka-Cassandra sink Dockerfile and configurations (Kafka Connect + Cassandra)
├── connect-elastic         # Kafka-Elasticsearch sink Dockerfile and configurations (Kafka Connect + Elasticsearch)
├── docs                    # Documentation files and notebooks
├── ingestion               # Data ingestion (python script + Kafka)
├── kubernetes              # Kubernetes configuration files (Kubernetes)
├── spark                   # Spark Dockerfile and python scripts (Spark + python script)
├── stream                  # Kafka stream application to filter and enrich the input data (Kafka Streaming)
├── .gitattribute           # .gitattribute file
├── .gitignore              # .gitignore file
├── docker-compose.yaml     # Base docker-compose file. Starts all the applications
├── LICENSE                 # Licence of the project
└── README.md               # This file
```

## Brief description
- This is a project created for the subject _Technologies for Advanced Programming_ or _TAP_ at the _university of Catania_ or _UniCT_.
- The idea is to showcase a simple ETL pipeline using some of the most widely known technologies in the big data fields.
- The main inspiration for this project was the [OpenDota project](https://www.opendota.com/), more specifically the _"core"_ part which is [opensource](https://github.com/odota/core).
- Raw data comes from the WebAPI provided by _Steam_ (Valve).

## Technologies used
| Step | Technology used |
| :-: | :-: |
| Data source | [Steam API](http://api.steampowered.com/IDOTA2Match_570/GetMatchHistoryBySequenceNum/V001/) |
| Data transport | [Apache Kafka](https://kafka.apache.org/) |
| Data processing | [Apache Kafka streams](https://kafka.apache.org/documentation/streams/) - [Apache Spark](https://spark.apache.org/) |
| Data storage | [Apache Cassandra](https://cassandra.apache.org/) - [Elasticsearch](https://www.elastic.co/enterprise-search) |
| Data visualization | [Kibana](https://www.elastic.co/kibana) |
| Programming language | [Python](https://www.python.org/) - [Java](https://www.java.com/)


## Pipeline
![pipeline](docs/img/Dotingestion2-Pipeline.svg)

| Index | Kafka topic | From - To |
| - | - | - |
| 1 | dota_raw | Steam Web API - Kafka |
| 2 | dota_raw | Kafka - Kafka Steaming |
| 3 | dota_single - dota_lineup | Kafka Streaming - Kafka |
| 4 | dota_single | Kafka - Cassandra |
| 5 | dota_single | Kafka - Elasticsearch |
| 6 | dota_lineup | Kafka - Spark |

## Quickstart local (Docker)

### System requirements
- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Steps
- To run the Elasticsearch container you may need to tweak the *vm.max_map_count* variable. See [here](https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html)
- Download [DataStax Apache Kafka® Connector](https://downloads.datastax.com/#akc) and place it in the _connect-cassandra_ directory
- Make sure you are in the root directory, with the _docker-compose.yaml_ file
- Create an _ingestion/settings.yaml_ file with the following values (see _ingestion/settings.yaml.example_)
  ```yaml
  # You need this to access the Steam Web API, which is used to fetch basic match data. You can safely use your main account to obtain the API key. You can request an API key here: https://steamcommunity.com/dev/apikey
  api_key: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
  # Steam Web API endpoint. You should not modify this unless you know what you are doing
  api_endpoint: http://api.steampowered.com/IDOTA2Match_570/GetMatchHistoryBySequenceNum/V001/?key={}&start_at_match_seq_num={}
  # Kafka topic the producer will send the data to. The Kafka streams consumer expects this topic
  topic: dota_raw
  # 3 possible settings can be placed here:
  # - The sequential match id of the first match you want to fetch
  # - 'cassandra', will fetch the last sequential match id in the cassandra database
  # - 'steam', will fetch the most recent sequential match id from the "history_endpoint"
  match_seq_num: 4976549000 | 'steam' | 'cassandra'
  # Steam API Web endpoint used when 'steam' value is placed in "match_seq_num"
  history_endpoint: https://api.steampowered.com/IDOTA2Match_570/GetMatchHistory/V001/key={}&matches_requested=1
  ```
  All the values present in the settings file can be overwritten by any environment variable whit the same name in all caps
- Start:
  ```bash
  docker-compose up
  ```
- Stop:
  ```bash
  docker-compose down
  ```

## Quickstart local (Kubernetes)

### System requirements
- [Docker](https://www.docker.com/get-started)
- [Kubernetes tool, like minikube](https://kubernetes.io/docs/tasks/tools/)

### Steps
- To run the Elasticsearch container you may need to tweak the *vm.max_map_count* variable. See [here](https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html)
- Make sure you are in the root directory, with the _all-in-one-deploy.yaml_ file
- Make sure to edit the _kubernetes/kafkaproducer-key.yaml_ file to add your [Steam Web API key](https://steamcommunity.com/dev/apikey). All the settings shown above will be determined by the environment variable whit the same name in all caps
- Start:
  ```bash
  kubectl apply -f all-in-one-deploy.yaml
  ```
- Stop:
  ```bash
  kubectl delete -f all-in-one-deploy.yaml
  ```

### Basic troubleshooting
- `docker exec -it <container-name> bash` Get a terminal into the running container
- `docker system prune` Cleans your system of any stopped containers, images, and volumes
- `docker-compose build` Rebuilds your containers (e.g. for database schema updates)
- `kubectl -n default rollout restart deploy` Restart all Kubernetes pods

## Resources
- [OpenDota](https://www.opendota.com/)
- [TeamFortress wiki](https://wiki.teamfortress.com/wiki/WebAPI/GetMatchDetails)
- [DataStax Apache Kafka Connector](https://docs.datastax.com/en/kafka/doc/kafka/kafkaIntro.html)
- [Structured Streaming Programming Guide](http://spark.apache.org/docs/latest/structured-streaming-programming-guide.html#foreachbatch)
- [Databricks: Deploying MLlib for Scoring in Structured Streaming](https://databricks.com/session/deploying-mllib-for-scoring-in-structured-streaming)
- [I used deep learning to predict DotA 2](https://www.reddit.com/r/DotA2/comments/gf1zgx/i_used_deep_learning_to_predict_dota_2_win/)
- [Elasticsearch: Using Docker images in production](https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html#docker-prod-prerequisites)
- [Elasticsearch Service Sink Connector for Confluent Platform](https://docs.confluent.io/kafka-connect-elasticsearch/current/index.html)
- [How to start multiple streaming queries in a single Spark application?](https://stackoverflow.com/questions/52762405/how-to-start-multiple-streaming-queries-in-a-single-spark-application)