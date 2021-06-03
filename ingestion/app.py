"""Dotingestion2 - Kafka producer"""
import os
import logging
import yaml
import requests
import time
import schedule
from confluent_kafka import Producer

# Setup the logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable that holds the match_seq_num to use in the API request
match_seq_num = None
config = {}

# Read the configuration file
if os.path.exists("settings.yaml"):
    with open("settings.yaml", 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

# Override with the environment settings
if os.getenv('MATCH_SEQ_NUM', None):
    config['match_seq_num'] = os.getenv('MATCH_SEQ_NUM')
if os.getenv('API_KEY', None):
    config['api_key'] = os.getenv('API_KEY')
if os.getenv('API_ENDPOINT', None):
    config['api_endpoint'] = os.getenv('API_ENDPOINT')
if os.getenv('TOPIC', None):
    config['topic'] = os.getenv('TOPIC')
if os.getenv('HISTORY_ENDPOINT', None):
    config['history_endpoint'] = os.getenv('HISTORY_ENDPOINT')


# Initialize the match_seq_num variable, depending on the value found in the configuration file
def get_match_seq_num(config: dict):
    if config['match_seq_num'] is None or config['match_seq_num'] == "steam":
        result = requests.get(config['history_endpoint'].format(config['api_key'])).json()
        res = result.get('result', None)
        matches = res.get('matches', None) if res is not None else None
        if matches:
            return matches[0]['match_seq_num']
    elif config['match_seq_num'] == "cassandra":
        from cassandra.cluster import Cluster
        cluster = Cluster(['cassandra'])
        session = cluster.connect("dota_ks")
        rows = session.execute('SELECT MAX(match_seq_num) FROM matches LIMIT 1')
        for row in rows:
            return row[0]
    elif config['match_seq_num'].isnumeric():
        return int(config['match_seq_num'])

    raise TypeError("match_seq_num must be either 'cassandra', 'steam', null or a integer")


# If there is an error with the kafka connection, log it
def delivery_report(err, decoded_message):
    if err is not None:
        logger.error("%s: decoded -> %s", err, decoded_message)


# Fetch the data from the Steam Web API and send the response to Kafka, saving only the match_seq_num of the last match
def confluent_producer():
    global match_seq_num
    try:
        result = requests.get(config['api_endpoint'].format(config['api_key'], match_seq_num))
        response = result.json()
        res = response.get('result', None)
        matches = res.get('matches', None) if res is not None else None
        if matches:
            producer = Producer({'bootstrap.servers': 'kafkaserver:9092', 'message.max.bytes': 1677722})
            producer.produce(config['topic'], result.text, callback=delivery_report)
            producer.flush()
            match_seq_num = matches[-1]['match_seq_num'] + 1
            logger.info("Flush completed. New match_seq_num: %d", match_seq_num)
        else:
            logger.warning("No matches found")
    except requests.exceptions.ConnectionError:
        return


# Initialize match_seq_num and keep requesting data from the the Steam Web API every 10 seconds
def main():
    global match_seq_num
    match_seq_num = get_match_seq_num(config)
    logger.info("Initialized match_seq_num: %d", match_seq_num)
    schedule.every(10).seconds.do(confluent_producer)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    main()
