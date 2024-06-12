import requests
import random
import csv
import time

API_KEY = 'RGAPI-9f9d85d9-3009-4396-99d5-b7cb2a175dcb'
gameName = 'T1 OK GOOD YES'
tagLine = 'NA1'  # Replace with the appropriate region
player_name = ['T1 OK GOOD YES',]
player_puuid = ['TEw5q-0eYfgQaxTZ8i9GIe2RmrCpv964ds400eSuxRKizO7UqprIe0-kf3rTbocBwaaCJGUUjQQf0A']

def get_match_history(api_key, puuid, region='americas'):
    match_type = "ranked"
    num_matches = 100
    url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?type={match_type}&start=0&count={num_matches}&api_key={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 429:
        print("Rate limit exceeded. Waiting before retrying...")
        time.sleep(120)  # Wait for 2 minutes before retrying
        return get_match_history(api_key, puuid, region)
    else:
        response.raise_for_status()

def get_match_info(match_id, api_key):
    url = f"https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 429:
        print("Rate limit exceeded. Waiting before retrying...")
        time.sleep(120)  # Wait for 2 minutes before retrying
        return get_match_info(match_id, api_key)
    else:
        response.raise_for_status()

while len(player_puuid) < 30000:
    rand_index = random.randint(0, len(player_puuid)-1)
    puuid = player_puuid[rand_index]
    try:
        matches = get_match_history(API_KEY, puuid)
        for match_id in matches:
            match_info = get_match_info(match_id, API_KEY)
            participants = match_info["info"]["participants"]
            for participant in participants:
                p_id = participant["puuid"]
                if p_id not in player_puuid:
                    player_puuid.append(p_id)
                    p_name = participant.get("riotIdGameName", "")
                    player_name.append(p_name)
                    print(f"{len(player_puuid)}/30000")
    except Exception as e:
        print(f"An error occurred: {e}")
    time.sleep(1.2)  # Add a delay between each loop iteration to avoid hitting the rate limit

# File path
file_path = "league_players.csv"

# Writing to CSV with UTF-8 encoding
with open(file_path, "w", newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    # Write the header
    writer.writerow(["Player Name", "PUUID"])
    # Write the data rows
    for name, puuid in zip(player_name, player_puuid):
        writer.writerow([name, puuid])