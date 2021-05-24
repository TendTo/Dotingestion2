/*
 * Copyright Confluent Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import org.apache.kafka.common.serialization.Serde;
import org.apache.kafka.common.serialization.Serdes;
import org.apache.kafka.streams.KafkaStreams;
import org.apache.kafka.streams.StreamsBuilder;
import org.apache.kafka.streams.StreamsConfig;
import org.apache.kafka.streams.kstream.Consumed;
import org.apache.kafka.streams.kstream.KStream;
import org.apache.kafka.streams.kstream.Produced;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Properties;

import org.json.JSONArray;
import org.json.JSONObject;

public class MatchesRefiner {

    static final String inputTopic = System.getenv("INPUT_TOPIC") == null ? "dota_raw" : System.getenv("INPUT_TOPIC");
    static final String outputTopicMatch = System.getenv("OUTPUT_TOPIC_MATCH") == null ? "dota_single"
            : System.getenv("OUTPUT_TOPIC_MATCH");
    static final String outputTopicLineup = System.getenv("OUTPUT_TOPIC_LINEUP") == null ? "dota_lineup"
            : System.getenv("OUTPUT_TOPIC_LINEUP");
    static final int PLAYER_SLOT_TEAM_MASK = 1 << 7;
    static final int PLAYER_SLOT_MASK = 7;

    /**
     * The Streams application as a whole can be launched like any normal Java
     * application that has a `main()` method.
     */
    public static void main(final String[] args) {
        final String bootstrapServers = args.length > 0 ? args[0] : "kafkaserver:9092";

        // Configure the Streams application.
        final Properties streamsConfiguration = getStreamsConfiguration(bootstrapServers);

        // Define the processing topology of the Streams application.
        final StreamsBuilder builder = new StreamsBuilder();
        createStream(builder);

        final KafkaStreams streams = new KafkaStreams(builder.build(), streamsConfiguration);

        // Always (and unconditionally) clean local state prior to starting the
        // processing topology.

        // The drawback of cleaning up local state prior is that your app must rebuilt
        // its local state from scratch, which
        // will take time and will require reading all the state-relevant data from the
        // Kafka cluster over the network.
        // Thus in a production scenario you typically do not want to clean up always as
        // we do here but rather only when it
        // is truly needed, i.e., only under certain conditions (e.g., the presence of a
        // command line flag for your app).
        // See `ApplicationResetExample.java` for a production-like example.
        streams.cleanUp();

        // Now run the processing topology via `start()` to begin processing its input
        // data.
        streams.start();

        // Add shutdown hook to respond to SIGTERM and gracefully close the Streams
        // application.
        Runtime.getRuntime().addShutdownHook(new Thread(streams::close));
    }

    /**
     * Configure the Streams application.
     *
     * Various Kafka Streams related settings are defined here such as the location
     * of the target Kafka cluster to use. Additionally, you could also define Kafka
     * Producer and Kafka Consumer settings when needed.
     *
     * @param bootstrapServers Kafka cluster address
     * @return Properties getStreamsConfiguration
     */
    static Properties getStreamsConfiguration(final String bootstrapServers) {
        final Properties streamsConfiguration = new Properties();
        // Give the Streams application a unique name. The name must be unique in the
        // Kafka cluster
        // against which the application is run.
        streamsConfiguration.put(StreamsConfig.APPLICATION_ID_CONFIG, "matches-refiner");
        streamsConfiguration.put(StreamsConfig.CLIENT_ID_CONFIG, "matches-refiner-client");
        // Where to find Kafka broker(s).
        streamsConfiguration.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        // Specify default (de)serializers for record keys and for record values.
        streamsConfiguration.put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, Serdes.String().getClass().getName());
        streamsConfiguration.put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, Serdes.String().getClass().getName());
        // Records should be flushed every 10 seconds. This is less than the default
        // in order to keep this example interactive.
        streamsConfiguration.put(StreamsConfig.COMMIT_INTERVAL_MS_CONFIG, 10 * 1000);
        return streamsConfiguration;
    }

    /**
     * Creates the stream matches stream
     *
     * @param builder StreamsBuilder to use
     */
    static void createStream(final StreamsBuilder builder) {
        final Serde<String> stringSerde = Serdes.String();

        final KStream<String, String> matches_raw = builder.stream(inputTopic, Consumed.with(stringSerde, stringSerde));

        final KStream<String, JSONObject> matches_single = matches_raw.flatMapValues(MatchesRefiner::splitMatches)
                .filter(MatchesRefiner::isValidMatch);

        // dota_single topic
        matches_single.flatMapValues(MatchesRefiner::enrichMatch).flatMapValues(MatchesRefiner::jsonToString)
                .to(outputTopicMatch, Produced.with(stringSerde, stringSerde));

        // dota_lineup topic
        matches_single.flatMapValues(MatchesRefiner::createLineup).flatMapValues(MatchesRefiner::jsonToString)
                .to(outputTopicLineup, Produced.with(stringSerde, stringSerde));
    }

    /**
     * Splits the matches received (max 10) and makes so each of them is a separate
     * entity
     * 
     * @param apiResponse Json response received from the Steam API
     * @return List of matches (max 10)
     */
    static List<JSONObject> splitMatches(String apiResponse) {
        JSONObject json = new JSONObject(apiResponse);
        JSONArray jsonArray = json.getJSONObject("result").getJSONArray("matches");
        ArrayList<JSONObject> jsonList = new ArrayList<>();
        for (int i = 0; i < jsonArray.length(); i++) {
            jsonList.add(jsonArray.getJSONObject(i));
        }
        return jsonList;
    }

    /**
     * Makes sure only valid matches with 10 human player are considered
     * 
     * @param key   match seq id (unused)
     * @param match Json response from the Steam API that represents a match
     * @return whether the match is to be considered
     */
    static boolean isValidMatch(String key, JSONObject match) {
        return match.getInt("human_players") == 10 && match.getInt("lobby_type") != -1;
    }

    /**
     * Enrich match data with some useful informations
     * 
     * @param match match to enrich
     * @return enriched match
     */
    static List<JSONObject> enrichMatch(JSONObject match) {
        ArrayList<JSONObject> matches = new ArrayList<>();
        // Add additional_units to each player if not present
        JSONArray players = match.getJSONArray("players");
        for (int i = 0; i < players.length(); i++) {
            JSONObject player = players.getJSONObject(i);
            if (player.isNull("additional_units")) {
                player.put("additional_units", new ArrayList<>());
            }
        }
        // Add picks_bans if not present
        if (match.isNull("picks_bans")) {
            match.put("picks_bans", new ArrayList<>());
        }
        // Add UTC timestamp
        long unixTime = match.getLong("start_time");
        Instant timestamp = Instant.ofEpochSecond(unixTime);
        match.put("start_timestamp", timestamp.toString());
        // Add location
        String location = DotaConstants.getRegion(match.getInt("cluster"));
        match.put("location", location);
        // Add vesion
        String version = DotaConstants.getVersion(match.getLong("start_time"));
        match.put("version", version);

        matches.add(match);
        return matches;
    }

    /**
     * Simplifies the data to get only the necessary informations about the lineup
     * 
     * @param match match to enrich
     * @return enriched match
     */
    static List<JSONObject> createLineup(JSONObject match) {
        ArrayList<JSONObject> lineups = new ArrayList<>();

        ArrayList<Integer> radiantLineup = new ArrayList<>();
        ArrayList<Integer> direLineup = new ArrayList<>();
        // Add additional_units to each player if not present
        JSONArray players = match.getJSONArray("players");
        for (int i = 0; i < players.length(); i++) {
            JSONObject player = players.getJSONObject(i);
            int hero = player.getInt("hero_id");
            if (player.getInt("player_slot") < 5) {
                radiantLineup.add(hero);
            } else {
                direLineup.add(hero);
            }
        }
        JSONObject lineup = new JSONObject();
        lineup.put("radiant_win", match.getBoolean("radiant_win"));
        lineup.put("radiant_lineup", radiantLineup);
        lineup.put("dire_lineup", direLineup);
        lineup.put("match_seq_num", match.getLong("match_seq_num"));

        lineups.add(lineup);
        return lineups;
    }

    /**
     * Converts each match data from a JSONObject to a string
     * 
     * @param match match
     * @return string representation of the JSONObject
     */
    static List<String> jsonToString(JSONObject match) {
        ArrayList<String> matches = new ArrayList<>();
        matches.add(match.toString());
        return matches;
    }
}