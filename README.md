# Dotingestion 2: there is no Dotingestion 1

## Project structure
```py
.
├── api                     # Rest api associated with the data (Springboot)
├── cassandra               # Cassandra Dockerfile and init script (Cassandra)
├── connect-cassandra       # Kafka-Cassandra sink Dockerfile and configurations (Kafka Connect + Cassandra)
├── connect-elastic         # Kafka-Elasticsearch sink Dockerfile and configurations (Kafka Connect + Elasticsearch)
├── docs                    # Documentation files
├── ingestion               # Data ingestion (python script + Kafka)
├── spark                   # Spark Dockerfile and python scripts (Spark + python script)
├── stream                  # Kafka stream application to filter and enrich the input data (Kafka Stream)
├── .gitignore              # .gitignore file
├── docker-compose.yaml     # Base docker compose file. Starts all the applications
├── LICENSE                 # Licence of the project
└── README.md               # This file
```

## Brief description
- This is a project created for the subject _Technologies for Advanced Programming_ or _TAP_ at the _univeristy of Catania_ or _UniCT_.
- The idea is to showcase a simple ETL pipeline using some of the most widly known technologies in the big data fileds.
- The main inspiration for this project was the [OpenDota project](https://www.opendota.com/), more specifically the _"core"_ part which is [opensource](https://github.com/odota/core).
- Raw data comes from the WebAPI provided by _Steam_ (Valve).

## Technologies used
| Step | Technology used |
| :-: | :-: |
| Data source | [Steam API](http://api.steampowered.com/IDOTA2Match_570/GetMatchHistoryBySequenceNum/V001/) |
| Data transport | [Apache Kafka](https://kafka.apache.org/) |
| Data process | [Apache Kafka streams](https://kafka.apache.org/documentation/streams/) - [Apache Spark](https://spark.apache.org/) |
| Data storage | [Apache Cassandra](https://cassandra.apache.org/) - [Elasticsearch](https://www.elastic.co/enterprise-search) |
| Data visualization | [Kibana](https://www.elastic.co/kibana) |
| Programming language | [Python](https://www.python.org/) - [Java](https://www.java.com/)


## Pipeline
![pipeline](docs/img/Dotingestion2-Pipeline.svg)

| Index | Kafka topic |
| - | - |
| 1 | dota_raw |
| 2 | dota_raw |
| 3 | dota_single |
| 4 | dota_single |
| 5 | dota_single |

## Quickstart (Docker)

### System requirements
- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Steps
- Download [spark-3.1.1-bin-hadoop2.7.tgz](https://www.apache.org/dyn/closer.lua/spark/spark-3.1.1/spark-3.1.1-bin-hadoop2.7.tgz) and place it in the _spark/setup_ directory
- Download [DataStax Apache Kafka® Connector](https://downloads.datastax.com/#akc) and place it in the _connect-cassandra_ directory
- Make sure you are in the root directory, with the _docker-compose.yaml_ file
- Create an _ingestion/settings.yaml_ file with the following values (see _ingestion/settings.yaml.example_)
  ```yaml
  # You need this in order to access the Steam Web API, which is used to fetch basic match data. You can safely use your main account to obtain the API key. You can request an API key here: https://steamcommunity.com/dev/apikey
  api_key: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
  # Steam Web API endpoint. You should not modify this, unless you know what you are doing
  api_endpoint: http://api.steampowered.com/IDOTA2Match_570/GetMatchHistoryBySequenceNum/V001/?key={}&start_at_match_seq_num={}
  # Kafka topic the producer will send the data to. The kafka streams consumer expects this topic
  topic: dota_raw
  # The sequential match id of the first match you want to fetch
  firt_match_id: 4976549000
  ```
- Start:
  ```bash
  docker-compose up
  ```
- Stop:
  ```bash
  docker-compose down
  ```

### Basic troubleshooting
- `docker exec -it <container-name> bash` Get a terminal into the running container
- `docker system prune` Cleans your system of any stopped containers, images, and volumes
- `docker-compose build` Rebuilds your containers (e.g. for database schema updates)

## Resources
- [OpenDota](https://www.opendota.com/)
- [TeamFortress wiki](https://wiki.teamfortress.com/wiki/WebAPI/GetMatchDetails)
- [Databricks: Deploying MLlib for Scoring in Structured Streaming](https://databricks.com/session/deploying-mllib-for-scoring-in-structured-streaming)