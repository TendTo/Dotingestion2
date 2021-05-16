#!/bin/bash

until curl -X PUT "http://elasticsearch:9200/dota_single/" -H 'Content-Type: application/json' -d'
      {
        "mappings": {
            "properties": {
            "barracks_status_dire": {
                "type": "long"
            },
            "barracks_status_radiant": {
                "type": "long"
            },
            "cluster": {
                "type": "long"
            },
            "dire_score": {
                "type": "long"
            },
            "duration": {
                "type": "long"
            },
            "engine": {
                "type": "long"
            },
            "first_blood_time": {
                "type": "long"
            },
            "flags": {
                "type": "long"
            },
            "game_mode": {
                "type": "long"
            },
            "human_players": {
                "type": "long"
            },
            "leagueid": {
                "type": "long"
            },
            "lobby_type": {
                "type": "long"
            },
            "location": {
                "type": "geo_point"
            },
            "match_id": {
                "type": "long"
            },
            "match_seq_num": {
                "type": "long"
            },
            "negative_votes": {
                "type": "long"
            },
            "picks_bans": {
                "properties": {
                "hero_id": {
                    "type": "long"
                },
                "is_pick": {
                    "type": "boolean"
                },
                "order": {
                    "type": "long"
                },
                "team": {
                    "type": "long"
                }
                }
            },
            "players": {
                "properties": {
                "ability_upgrades": {
                    "properties": {
                    "ability": {
                        "type": "long"
                    },
                    "level": {
                        "type": "long"
                    },
                    "time": {
                        "type": "long"
                    }
                    }
                },
                "account_id": {
                    "type": "long"
                },
                "additional_units": {
                    "properties": {
                    "backpack_0": {
                        "type": "long"
                    },
                    "backpack_1": {
                        "type": "long"
                    },
                    "backpack_2": {
                        "type": "long"
                    },
                    "item_0": {
                        "type": "long"
                    },
                    "item_1": {
                        "type": "long"
                    },
                    "item_2": {
                        "type": "long"
                    },
                    "item_3": {
                        "type": "long"
                    },
                    "item_4": {
                        "type": "long"
                    },
                    "item_5": {
                        "type": "long"
                    },
                    "item_neutral": {
                        "type": "long"
                    },
                    "unitname": {
                        "type": "text",
                        "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 256
                        }
                        }
                    }
                    }
                },
                "assists": {
                    "type": "long"
                },
                "backpack_0": {
                    "type": "long"
                },
                "backpack_1": {
                    "type": "long"
                },
                "backpack_2": {
                    "type": "long"
                },
                "deaths": {
                    "type": "long"
                },
                "denies": {
                    "type": "long"
                },
                "gold": {
                    "type": "long"
                },
                "gold_per_min": {
                    "type": "long"
                },
                "gold_spent": {
                    "type": "long"
                },
                "hero_damage": {
                    "type": "long"
                },
                "hero_healing": {
                    "type": "long"
                },
                "hero_id": {
                    "type": "long"
                },
                "item_0": {
                    "type": "long"
                },
                "item_1": {
                    "type": "long"
                },
                "item_2": {
                    "type": "long"
                },
                "item_3": {
                    "type": "long"
                },
                "item_4": {
                    "type": "long"
                },
                "item_5": {
                    "type": "long"
                },
                "item_neutral": {
                    "type": "long"
                },
                "kills": {
                    "type": "long"
                },
                "last_hits": {
                    "type": "long"
                },
                "leaver_status": {
                    "type": "long"
                },
                "level": {
                    "type": "long"
                },
                "player_slot": {
                    "type": "long"
                },
                "scaled_hero_damage": {
                    "type": "long"
                },
                "scaled_hero_healing": {
                    "type": "long"
                },
                "scaled_tower_damage": {
                    "type": "long"
                },
                "tower_damage": {
                    "type": "long"
                },
                "xp_per_min": {
                    "type": "long"
                }
                }
            },
            "positive_votes": {
                "type": "long"
            },
            "pre_game_duration": {
                "type": "long"
            },
            "radiant_score": {
                "type": "long"
            },
            "radiant_win": {
                "type": "boolean"
            },
            "start_time": {
                "type": "long"
            },
            "start_timestamp": {
                "type": "date"
            },
            "tower_status_dire": {
                "type": "long"
            },
            "tower_status_radiant": {
                "type": "long"
            },
            "version": {
                "type": "text",
                "fields": {
                "keyword": {
                    "type": "keyword",
                    "ignore_above": 256
                }
                }
            }
            }
        }
        }'; do
  echo "curl: Elasticsearch is unavailable - retry later"
  sleep 2
done &

exec /bin/connect-standalone /etc/kafka/connect-standalone.properties /etc/kafka/elsaticsearch-sink.properties
