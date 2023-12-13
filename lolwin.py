import requests
import pandas as pd
import joblib

# Hide for hiding purposes
API_KEY = 'RGAPI-b65fc45d-52a8-443b-a100-eee4759331cd'

# Get encrypted summoner ID
def get_summoner_id(summoner_name, api_key):
    url = f'https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}?api_key={api_key}'
    response = requests.get(url)
    data = response.json()
    return data['puuid']

# Get player's match history
def get_matchlist(summoner_id, api_key):
    url = f'https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{summoner_id}/ids?api_key={api_key}'
    response = requests.get(url)
    data = response.json()
    return data

# Get match data for specific game
def get_match_data(match_id, api_key):
    url = f'https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline?api_key={api_key}'
    response = requests.get(url)
    data = response.json()
    return data

def get_10_minute_stats(timeline):
    features = {
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
    while timeline['frames'][i]['timestamp'] < 600000:
        i+=1
    
    for frame in timeline['frames']:
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

def main():
    summoner_name = input("Enter summoner name: ")
    game = int(input("Choose game (0 being the most recent): "))

    summoner_id = get_summoner_id(summoner_name, API_KEY)
    matchlist = get_matchlist(summoner_id, API_KEY)

    match_id = matchlist[game]
    match_data = get_match_data(match_id, API_KEY)

    test_instance = get_10_minute_stats(match_data['info'])

    # Make a prediction for the test instance based on the trained model
    prediction = joblib.load('model.joblib').predict(test_instance)
    print(f"Prediction: {'Blue Wins' if prediction[0] == 1 else 'Blue Loses'}")

if __name__ == "__main__":
    main()
