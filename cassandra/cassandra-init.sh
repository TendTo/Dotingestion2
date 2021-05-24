#!/bin/bash

if [[ ! -z "$CASSANDRA_KEYSPACE" && ! -z "$CASSANDRA_MATCH_TABLE"  && $1 = 'cassandra' ]]; then
  # Create default keyspace for single node cluster, some UDTs and the table schema
  CQL="CREATE KEYSPACE $CASSANDRA_KEYSPACE WITH REPLICATION = {'class': 'SimpleStrategy', 'replication_factor': 1};
    USE $CASSANDRA_KEYSPACE;

    CREATE TABLE IF NOT EXISTS $CASSANDRA_MATCH_TABLE (
      radiant_win boolean,
      duration int,
      pre_game_duration int,
      start_time bigint,
      start_timestamp timestamp,
      match_id bigint,
      match_seq_num bigint,
      tower_status_radiant int,
      tower_status_dire int,
      barracks_status_radiant int,
      barracks_status_dire int,
      location text,
      cluster int,
      first_blood_time int,
      lobby_type int,
      human_players int,
      leagueid int,
      positive_votes int,
      negative_votes int,
      game_mode int,
      flags int,
      engine int,
      radiant_score int,
      dire_score int,
      version text,
      players text,
      picks_bans text,
      PRIMARY KEY(match_id, match_seq_num)
    )
    WITH CLUSTERING ORDER BY (match_seq_num DESC);"
  until echo $CQL | cqlsh; do
    echo "cqlsh: Cassandra is unavailable - retry later"
    sleep 2
  done &
fi

exec /docker-entrypoint.sh "$@"