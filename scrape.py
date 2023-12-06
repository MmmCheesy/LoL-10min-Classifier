import requests
import pandas as pd
import joblib
import random
import time

API_KEY = "RGAPI-285420a3-4630-4457-8947-93fd54cf65d6"
ELO_TIER = "EMERALD"

def get_random_players():
    response = requests.get(f"https://na1.api.riotgames.com/lol/league/v4/entries/RANKED_SOLO_5x5/{ELO_TIER}/I?page=1&api_key={API_KEY}")
    players = response.json()
    return [player["summonerName"] for player in players]
    
def get_summoner_id(summoner_name):
    response = requests.get(f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}?api_key={API_KEY}")
    return response.json()['puuid']

def get_match_list(summoner_id):
    response = requests.get(f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{summoner_id}/ids?api_key={API_KEY}")
    return response.json()
    
def get_outcome(match_id):
    response = requests.get(f"https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline?api_key={API_KEY}")
    return response.json()
    
def parse_outcome(match):
    features = {
        'gameId': match['gameId'],           #√
        'blueWins': 0,                       #√
        'blueWardsPlaced': 0,                #√
        'blueWardsDestroyed': 0,             #√
        'blueFirstBlood': 0,                 #√
        'blueKills': 0,                      #√
        'blueDeaths': 0,                     #√
        'blueAssists': 0,                    #√
        'blueEliteMonsters': 0,              #√
        'blueDragons': 0,                    #√
        'blueHeralds': 0,                    #√
        'blueTowersDestroyed': 0,            #√
        'blueTotalGold': 0,                  #√
        'blueAvgLevel': 0,                   #√
        'blueTotalExperience': 0,            #√
        'blueTotalMinionsKilled': 0,         #√
        'blueTotalJungleMinionsKilled': 0,   #√
        'blueGoldDiff': 0,                   #√
        'blueExperienceDiff': 0,             #√
        'blueCSPerMin': 0,                   #√
        'blueGoldPerMin': 0,                 #√
        'redWardsPlaced': 0,                 #√
        'redWardsDestroyed': 0,              #√
        'redFirstBlood': 0,                  #√
        'redKills': 0,                       #√
        'redDeaths': 0,                      #√
        'redAssists': 0,                     #√
        'redEliteMonsters': 0,               #√
        'redDragons': 0,                     #√
        'redHeralds': 0,                     #√
        'redTowersDestroyed': 0,             #√
        'redTotalGold': 0,                   #√
        'redAvgLevel': 0,                    #√
        'redTotalExperience': 0,             #√
        'redTotalMinionsKilled': 0,          #√
        'redTotalJungleMinionsKilled': 0,    #√
        'redGoldDiff': 0,                    #√
        'redExperienceDiff': 0,              #√
        'redCSPerMin': 0,                    #√
        'redGoldPerMin': 0,                  #√
    }
    
    i=0
    try:
        while match['frames'][i]['timestamp'] < 600000:
            i+=1
    except:
        return None
        
    for event in match['frames'][-1].get('events', []):
        if event['type'] == 'GAME_END':
            if event['winningTeam'] == 100:
                features['blueWins'] = 1
            else:
                features['blueWins'] = 0
    
    for frame in match['frames']:
        # Get stats after 10 mintes timestamp
        if frame['timestamp'] > 600000:
        
            features['blueEliteMonsters'] = features['blueDragons'] + features['blueHeralds']
            features['redEliteMonsters'] = features['redDragons'] + features['redHeralds']
            
            stats = frame.get('participantFrames', [])
            
            for participant_id, stats in stats.items():
                team_id = 'blue' if int(participant_id) <= 5 else 'red'

                features[f'{team_id}TotalGold'] += stats.get('totalGold', 0)
                features[f'{team_id}TotalExperience'] += stats.get('xp', 0)
                features[f'{team_id}TotalMinionsKilled'] += stats.get('minionsKilled', 0)
                features[f'{team_id}TotalJungleMinionsKilled'] += stats.get('jungleMinionsKilled', 0)
                features[f'{team_id}AvgLevel'] += stats.get('level', 0)

            features['blueGoldDiff'] = features['blueTotalGold'] - features['redTotalGold']
            features['redGoldDiff'] = features['redTotalGold'] - features['blueTotalGold']
            features['blueExperienceDiff'] = features['blueTotalExperience'] - features['redTotalExperience']
            features['redExperienceDiff'] = features['redTotalExperience'] - features['blueTotalExperience']

            features['blueCSPerMin'] = (features['blueTotalMinionsKilled'] + features['blueTotalJungleMinionsKilled']) / 10
            features['redCSPerMin'] = (features['redTotalMinionsKilled'] + features['redTotalJungleMinionsKilled']) / 10

            features['blueGoldPerMin'] = features['blueTotalGold']  / 10
            features['redGoldPerMin'] = features['redTotalGold']  / 10
            
            features['blueAvgLevel'] = features['blueAvgLevel'] / 5
            features['redAvgLevel'] = features['redAvgLevel'] / 5
            
            break
          
        # Get stats that aren't automatically added up
        for event in frame.get('events', []):
            team_id = 'blue' if event.get('killerId', 0) <= 5 else 'red'

            if event['type'] == 'WARD_PLACED':
                team_id = 'blue' if event.get('creatorId', 0) <= 5 else 'red'
                team = 'blueWardsPlaced' if team_id == 'blue' else 'redWardsPlaced'
                features[team] += 1

            elif event['type'] == 'WARD_KILL':
                team = 'blueWardsDestroyed' if team_id == 'blue' else 'redWardsDestroyed'
                features[team] += 1

            elif event['type'] == 'BUILDING_KILL' and event['buildingType'] == 'TOWER_BUILDING':
                team = 'blueTowersDestroyed' if team_id == 'blue' else 'blueTowersDestroyed'
                features[team] += 1

            elif event['type'] == 'ELITE_MONSTER_KILL':
                if event['monsterType'] == 'DRAGON':
                    team = 'blueDragons' if team_id == 'blue' else 'redDragons'
                    features[team] += 1
                elif event['monsterType'] == 'RIFTHERALD':
                    team = 'blueHeralds' if team_id == 'blue' else 'redHeralds'
                    features[team] += 1

            elif event['type'] == 'CHAMPION_KILL':
                team = 'blueKills' if team_id == 'blue' else 'redKills'
                features[team] += 1

                victim_team_id = 'blue' if event.get('victimId', 0) <= 5 else 'red'
                victim_team = 'blueDeaths' if victim_team_id == 'blue' else 'redDeaths'
                features[victim_team] += 1
                
                if features['blueFirstBlood'] == 0 and features['redFirstBlood'] == 0:
                    if team_id == 'blue':
                        features['blueFirstBlood'] = 1
                    else:
                        features['redFirstBlood'] = 1

                assist_ids = event.get('assistingParticipantIds', [])
                for assist_id in assist_ids:
                    assist_team_id = 'blue' if assist_id <= 5 else 'red'
                    assist_team = 'blueAssists' if assist_team_id == 'blue' else 'redAssists'
                    features[assist_team] += 1

    return pd.DataFrame([features])

start_time = time.time()
random_players = random.sample(get_random_players(), 5)

all_matches = []
for player in random_players:
    player_id = get_summoner_id(player)
    recent_matches = get_match_list(player_id)
    for match in recent_matches:
        outcome = get_outcome(match)
        data = parse_outcome(outcome['info'])
        all_matches.append(data)
        time.sleep(1)

cat = pd.concat(all_matches, ignore_index=True)
cat.to_csv('mydata.csv', index=False)

print(f"Execution time: {time.time() - start_time} seconds")
