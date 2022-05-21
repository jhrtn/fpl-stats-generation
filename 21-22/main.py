#%%
from pprint import pprint
import requests
import pandas as pd
import numpy as np
import json
import os

# %%

BASE_DIR = "data"
GW_INFO_EXT = "_gw_info.csv"
TEAM_INFO_EXT = "_team_info_detailed.csv"

NUM_GAMEWEEKS = 38
MAX_PLAYER_MINUTES = NUM_GAMEWEEKS * 90
MAX_SQUAD_MINUTES = MAX_PLAYER_MINUTES * 11 + (4 * 90 * 2) # extra 4 players for bench boost
TOTAL_PLAYERS = -1

def get_gw_info(player_id):
  player_history_url = f'https://fantasy.premierleague.com/api/entry/{player_id}/history/'
  data = requests.get(player_history_url).json()
  current = data['current']
  chips = data['chips']
  for gw in current:
    for chip in chips:
      if gw['event'] == chip['event']:
        gw['used_chip'] = chip['name']
  
  return pd.DataFrame(current)
  
def get_name(row):
    name = list(filter(lambda p: p['player_id'] == row['id'], player_info))[0]['name']
    return name

def calc_win_perct(row):
    return round((row.iat[0] / 38) * 100, 2)

def format_name(name: str):
  formatted_name = name.replace(' ', '_').lower()
  return formatted_name

def check_position_percentage(pos, total_players):
  pos_perct = (int(pos) / total_players) * 100
  pos_perct = round(pos_perct, 2)
  return str(pos_perct) + "%"

def calc_captain_points(player_id):
  gw = 1
  df = pd.DataFrame()
  captain_points = 0
  while gw <= 38:
    req_path = f'https://fantasy.premierleague.com/api/entry/{player_id}/event/{gw}/picks/#/'
    team = requests.get(req_path).json()
    played_players = list(filter(lambda element: element['multiplier'] > 0, team['picks']))
    captain = list(filter(lambda player: player['multiplier'] > 1, played_players))
    if len(captain) == 1:
      captain = captain[0]
      gw_data_url = f'https://fantasy.premierleague.com/api/event/{gw}/live/#/'
      gw_api_data = requests.get(gw_data_url).json()
      captain_gw_data = list(filter(lambda element: element['id'] == captain['element'], gw_api_data['elements']))[0]
      captain_points += captain_gw_data['stats']['total_points'] * captain['multiplier']
    
    gw += 1
  print(f'total captain points for {name}: {captain_points}\n')

  return captain_points

def get_full_squad_breakdown(player_id):
  cols = ['manager', 'manager_id', 'gw', 'total_points', 'first_name', 'last_name', 'team_name', 'in_dreamteam', 'minutes', 'goals_scored', 'clean_sheet', 'is_captain', 'player_id', 'team_id', 'red_cards', 'yellow_cards']
  teams = bootstrap_data['teams']
  gw = 1
  df = pd.DataFrame()
  while gw <= 2:
    squad = requests.get(f'https://fantasy.premierleague.com/api/entry/{player_id}/event/{gw}/picks/#/').json()
    played_players = list(filter(lambda element: element['multiplier'] > 0, squad['picks']))
    played_players_list = []
    for player in played_players:
      print(player)
      gw_data_url = f'https://fantasy.premierleague.com/api/event/{gw}/live/#/'
      gw_api_data = requests.get(gw_data_url).json()
      player_gw_detail = list(filter(lambda p: p['id'] == player['element'], gw_api_data['elements']))[0]
      player_detail = list(filter(lambda p: p['id'] == player['element'], bootstrap_elements))[0]
      played_players_list = {
        'manager': name,
        'manager_id': player_id,
        'gw': gw,
        'player_id': player_gw_detail['id'],
        'total_points': player_gw_detail['stats']['total_points'],
        'points_multiplier': player['multiplier'],
        'in_dreamteam': player_gw_detail['stats']['in_dreamteam'],
        'first_name': player_detail['first_name'],
        'second_name': player_detail['second_name'],
        'red_cards': player_gw_detail['stats']['red_cards'],
        'yellow_cards': player_gw_detail['stats']['yellow_cards'],
        'minutes': player_gw_detail['stats']['minutes'],
        'goals_scored': player_gw_detail['stats']['goals_scored'],
        'clean_sheet': player_gw_detail['stats']['clean_sheets'],
        'is_captain': player['multiplier'] > 1,
        'team_id': player_detail['team'],
        'team_name': list(filter(lambda team: team['id'] == player_detail['team'], teams))[0]['name'],
      }
      df = df.append(played_players_list, ignore_index=True)
    gw += 1
  return df

#%%
# get all global data to use in stats generation
classic_league_id = 603941
h2h_league_id = 652857

league_url = f'https://fantasy.premierleague.com/api/leagues-classic/{classic_league_id}/standings/'
h2h_league_url = f'https://fantasy.premierleague.com/api/leagues-h2h/{h2h_league_id}/standings/'
bootstrap_url = 'https://fantasy.premierleague.com/api/bootstrap-static/#/'

classic_data = requests.get(league_url).json()
h2h_data = requests.get(league_url).json()
classic_reults = classic_data['standings']['results']
h2h_results = h2h_data['standings']['results']

bootstrap_data = requests.get(bootstrap_url).json()
bootstrap_elements = bootstrap_data['elements']

# %%

for index, player in enumerate(classic_reults):
  id = player['entry']
  if (list(map(lambda p: p['entry'] == id, h2h_results))):
    if (index > 0): break
    name = player['player_name']
    print(f'running for {name}')
    
    team_info = requests.get(f'https://fantasy.premierleague.com/api/entry/{id}/').json()
    
    current = {
      'manager': name,
      'player_id': id,
      'team_name': player['entry_name'],
      'total_score': team_info['summary_overall_points'],
      'final_overall_rank': team_info['summary_overall_rank'],      
    }

    gw_info = get_gw_info(id)
    print(gw_info)

    # print(current)
  else:
    name = player['player_name']
    print(f'player {name} is not in both leagues')

  
  # %%

