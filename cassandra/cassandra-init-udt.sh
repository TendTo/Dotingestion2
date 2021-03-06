#!/bin/bash

if [[ ! -z "$CASSANDRA_KEYSPACE" && ! -z "$CASSANDRA_MATCH_TABLE"  && $1 = 'cassandra' ]]; then
  # Create default keyspace for single node cluster, some UDTs and the table schema
  CQL="CREATE KEYSPACE $CASSANDRA_KEYSPACE WITH REPLICATION = {'class': 'SimpleStrategy', 'replication_factor': 1};
    USE $CASSANDRA_KEYSPACE;
    CREATE TYPE Pick_Ban (
      is_pick boolean,
      hero_id int,
      team int,
      \"order\" int,
    );

    CREATE TYPE Ability_Upgrade (
      ability int,
      time int,
      level int,
    );

    CREATE TYPE Additional_Unit (
      unitname text,
      item_0 int,
      item_1 int,
      item_2 int,
      item_3 int,
      item_4 int,
      item_5 int,
      backpack_0 int,
      backpack_1 int,
      backpack_2 int,
      item_neutral int,
    );

    CREATE TYPE Player (
      account_id bigint,
      player_slot int,
      hero_id int,
      item_0 int,
      item_1 int,
      item_2 int,
      item_3 int,
      item_4 int,
      item_5 int,
      backpack_0 int,
      backpack_1 int,
      backpack_2 int,
      item_neutral int,
      kills int,
      deaths int,
      assists int,
      leaver_status int,
      last_hits int,
      denies int,
      gold_per_min int,
      xp_per_min int,
      level int,
      hero_damage int,
      tower_damage int,
      hero_healing int,
      gold int,
      gold_spent int,
      scaled_hero_damage int,
      scaled_tower_damage int,
      scaled_hero_healing int,
      ability_upgrades list<frozen<Ability_Upgrade>>,
      additional_units list<frozen<Additional_Unit>>,
    );

    CREATE TABLE IF NOT EXISTS matches (
      radiant_win boolean,
      duration int,
      pre_game_duration int,
      start_time bigint,
      start_timestamp timestamp,
      match_id bigint PRIMARY KEY,
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
      players list<frozen<Player>>,
      picks_bans list<frozen<Pick_Ban>>,
    );"
  until echo $CQL | cqlsh; do
    echo "cqlsh: Cassandra is unavailable - retry later"
    sleep 2
  done &
fi

exec /docker-entrypoint.sh "$@"