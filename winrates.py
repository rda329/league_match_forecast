import requests
import time
import random
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def get_puuid(player_name, API_KEY):
    try:
        url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{player_name}/NA1?api_key={API_KEY}"
        response = requests.get(url)
        response_json = response.json()
        puuid = response_json["puuid"]
        return puuid
    except KeyError:
        return None

def get_match_history(api_key, puuid, region='americas', num_matches=100):
    match_type = "ranked"
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

def individual_winrate(puuid, player_name, API_KEY):
    # Set Chrome options to reduce handshake attempts
    chrome_options = Options()
    chrome_options.add_argument("--reduce-security-for-testing")  # This is not an actual Chrome option, it's just an example
    chrome_options.add_argument("--disable-http2")  # Another example option, real options depend on the requirement

    # Initialize the WebDriver with options
    driver = webdriver.Chrome(options=chrome_options)

    try:
        formatted_player_name = player_name.replace(' ', '%20')  # Encode spaces as %20
        url = f"https://www.op.gg/summoners/na/{formatted_player_name}-NA1?queue_type=SOLORANKED"
        driver.get(url)

        # Wait for the element to be present, up to 20 seconds
        element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div[9]/div[2]/div[2]/div[1]/div[2]/div[1]/div[2]/strong"))
        )
        
        # Once the element is present, extract the text
        try:
            element_value = element.text
            value = float(element_value)
            return value
        except ValueError as e:
            return 50
        except Exception as e:
            return 50
    except Exception as e:
        return 50
    finally:
        driver.quit()


def get_winrate_by_champion(champion_name):
    try:
        # Open the CSV file and read its contents
        with open('champion_winrate.csv', mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            # Iterate over each row in the CSV file
            for row in reader:
                # Check if the champion name matches the input
                if row['champion'] == champion_name:
                    # Check if 'winrate(%)' exists in the row
                    if 'winrate(%)' in row:
                        # Return the winrate corresponding to the champion
                        return float(row['winrate(%)'])  # Convert to float
                    else:
                        print(f"Winrate data missing for champion '{champion_name}'.")
                        return None
            # If the champion is not found, return None
            print(f"Champion '{champion_name}' not found.")
            return None
    except FileNotFoundError:
        print("CSV file 'champion_winrate.csv' not found.")
        return None

def teams_weighted_winrate(rand_match_id, API_KEY):
    members_wr = []
    champions_wr = []
    match_info = get_match_info(rand_match_id, API_KEY)
    participants = match_info["info"]["participants"]
    for i in range(5):  # Loop only for indices 0 to 4
        participant = participants[i]
        player_name = participant.get("riotIdGameName")  # Use .get() to avoid KeyError
        if player_name is not None:
            player_puuid = get_puuid(player_name, API_KEY)
            if player_puuid is not None:
                player_wr = individual_winrate(player_puuid, player_name, API_KEY)
                if player_wr is not None:
                    members_wr.append(player_wr)
                players_champion = participant.get("championName")
                if players_champion is not None:
                    players_champion_wr = get_winrate_by_champion(players_champion)
                    if players_champion_wr is not None:
                        champions_wr.append(players_champion_wr)
    
    if members_wr:  # Check if members_wr is not empty
        percentage1 = sum(members_wr) / len(members_wr)
    else:
        percentage1 = 0
    
    weight1 = 0.7  # 70%
    
    if champions_wr:  # Check if champions_wr is not empty
        percentage2 = sum(champions_wr) / len(champions_wr)
    else:
        percentage2 = 0
    
    weight2 = 0.3  # 30%
    
    # Calculate the weighted average percentage
    weighted_average = (percentage1 * weight1 + percentage2 * weight2) / (weight1 + weight2)
    
    match_result = participants[0]["win"]
    if match_result == "false":
        match_result = 0
    elif match_result == "true":
        match_result = 1
    print(members_wr,"member_wr")
    print(champions_wr,"champ_wr")
    return [weighted_average, match_result]



def read_puuid_from_csv(filename):
    puuid_list = []
    try:
        # Open the CSV file and read its contents
        with open(filename, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            # Iterate over each row in the CSV file
            for row in reader:
                # Extract the PUUID from the row and append it to the list
                puuid_list.append(row['PUUID'])
    except FileNotFoundError:
        print(f"CSV file '{filename}' not found.")
    return puuid_list

def update_average_in_csv(filename, puuid, API_KEY):
    try:
        # Open the original CSV file and read its contents
        with open(filename, mode='r', encoding='utf-8') as file:
            rows = list(csv.DictReader(file))
        
        # Find the row matching the puuid
        for row in rows:
            if row['PUUID'] == puuid and row['match_weighted_average(%)'] == 'NA':
                match_lst = get_match_history(API_KEY, puuid)
                rand_index = random.randint(0, len(match_lst) - 1)
                rand_match_id = match_lst[rand_index]
                weighted_average = teams_weighted_winrate(rand_match_id, API_KEY)
                time.sleep(1)  # Add a delay between API requests to prevent rate limiting
                if weighted_average[0] is None:
                    row['match_weighted_average(%)'] = "NaN"
                else:
                    row['match_weighted_average(%)'] = weighted_average[0]
                
                if weighted_average[1] is None:
                    row['match_result'] = "NaN"
                else:
                    row['match_result'] = weighted_average[1]
                break

        # Get the fieldnames from the first row of the original file
        fieldnames = rows[0].keys()

        # Filter out dictionaries with keys not present in fieldnames
        filtered_rows = [{key: row[key] for key in fieldnames} for row in rows]

        # Write the updated content back to the original CSV file
        with open(filename, mode='w', encoding='utf-8', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(filtered_rows)
    except FileNotFoundError:
        print(f"CSV file '{filename}' not found.")

# Usage example
API_KEY = 'RGAPI-48515295-6889-4e95-ba61-eaa92490fab3'
filename = 'league_players.csv'  # Replace 'league_players.csv' with the actual filename
puuid_list = read_puuid_from_csv(filename)
for count, puuid in enumerate(puuid_list):
    update_average_in_csv(filename, puuid, API_KEY)
    print(f"{count+1}/{len(puuid_list)}")