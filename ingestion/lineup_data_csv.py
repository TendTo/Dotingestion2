"""Dotingestion2 - Create a dataset to train the model. Saves it to a csv file"""
from time import sleep
import logging
import yaml
import requests
import schedule

# Setup the logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable that holds the match_seq_num to use in the API request
match_seq_num = None


# Store only the lineup data in a csv file
def store_data():
    global match_seq_num
    with open("settings.yaml", 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    rows = []
    match_seq_num = match_seq_num if match_seq_num else config['match_seq_num']
    result = requests.get(config['api_endpoint'].format(config['api_key'], match_seq_num))
    if result.status_code == 200:
        for match in result.json()['result']['matches']:
            if match['human_players'] != 10 or match['game_mode'] in (8, 11, 12, 15, 18, 20, 21):
                continue
            match_seq_num = match['match_seq_num'] + 1
            radiant_pick = []
            dire_pick = []
            for player in match['players']:
                if player['player_slot'] < 5:
                    radiant_pick.append(str(player['hero_id']))
                else:
                    dire_pick.append(str(player['hero_id']))
            rows.append(
                f"{','.join(radiant_pick)},{','.join(dire_pick)},{'true' if match['radiant_win'] else 'false'},{match['match_seq_num']}\n"
            )
        with open("data.csv", 'a+') as f:
            f.write("".join(rows))

    logger.info("Flush completed. New match_seq_num: %d", match_seq_num)


# Requesting data from the the Steam Web API every X seconds
def main():
    schedule.every(3).seconds.do(store_data)
    while True:
        schedule.run_pending()
        sleep(1)


if __name__ == '__main__':
    main()
