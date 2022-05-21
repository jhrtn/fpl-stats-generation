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
  
  if not (os.path.exists(BASE_DIR)):
    os.mkdir(BASE_DIR)
  full_path = os.path.join(BASE_DIR, str(player_id) + GW_INFO_EXT)
  df = pd.DataFrame(current)
  df.to_csv(full_path, index=False)
  
  return df
  
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
  
  
  if not (os.path.exists(BASE_DIR)):
    os.mkdir(BASE_DIR)
  full_path = os.path.join(BASE_DIR, str(player_id) + TEAM_INFO_EXT)
  df.to_csv(full_path, index=False)

  return df

def get_gw_path(id): return f'{BASE_DIR}/{id}{GW_INFO_EXT}'
def get_team_info_path(id): return f'{BASE_DIR}/{id}{TEAM_INFO_EXT}'

def get_chip_info(gw_data):
  only_chip_weeks = 0
  # manager used a chip
  if 'used_chip' in gw_data:
    only_chip_weeks = gw_data[gw_data['used_chip'].notnull()]
    first_chip = only_chip_weeks.sort_values(['event'], ascending=True)[:1]
    first_chip_gw = first_chip['event'].iat[0]
    chip_type = first_chip['used_chip'].iat[0]
    last_chip = only_chip_weeks.sort_values(['event'], ascending=True)[-1:]
    last_chip_gw = last_chip['event'].iat[0]
    last_chip_type = last_chip['used_chip'].iat[0]

    chip = 'wildcard'
    wildcard_gw_nums = list(gw_data.loc[gw_data['used_chip'] == chip]['event'])
    if len(wildcard_gw_nums) > 0:
      for gw in wildcard_gw_nums:
        gw_index = gw - 1
        gw_count = 1
        avg_before_wildcard = round(gw_data[gw_index-gw_count:gw_index]['points'].mean(),1)
        avg_after_wildcard = round(gw_data[gw_index:gw_index+gw_count]['points'].mean(), 1)
        wildcard_data = {
          'name': name, 
          'gw': gw, 
          f'avg_before_wildcard': avg_before_wildcard, 
          f'avg_after_wildcard': avg_after_wildcard,
          'diff': avg_after_wildcard - avg_before_wildcard,
          'perct_change': round(((avg_after_wildcard - avg_before_wildcard) / avg_before_wildcard) * 100, 2)
        }
  else:
    # no chips used
    only_chip_weeks = []
    first_chip = -1
    first_chip_gw = -1
    chip_type = -1
    last_chip = -1
    last_chip_gw = -1
    last_chip_type = -1

  return only_chip_weeks, first_chip, first_chip_gw, chip_type, last_chip, last_chip_gw, last_chip_type
  
def get_captain_info(team_data):
  cap_points_zip = list(zip(team_data[team_data['is_captain'] == True]['total_points'], team_data[team_data['is_captain'] == True]['points_multiplier']))
  captain_points = sum(list(map(lambda p: p[0] * p[1], cap_points_zip)))
  
  captains = team_data[team_data['is_captain'] == True]
  most_picked_captain_id = captains['player_id'].value_counts().index[0]
  num_times_picked = captains['player_id'].value_counts().tolist()[0]
  most_picked_captain = list(filter(lambda p: p['id'] == most_picked_captain_id, bootstrap_elements))[0]['web_name']
  return most_picked_captain, num_times_picked, captain_points

def get_unique_squad_players(id, team_data, manager_ids):
  # TODO: do some verification that all relavent files are in folder, 
  # otherwise, use generate_files() to get them all

  unique_player_ids = team_data['player_id'].drop_duplicates().tolist()
  print(manager_ids)
  manager_ids.remove(id)
  for m_id in manager_ids:
    try:
      f = open(get_team_info_path(m_id))
      manager_team_info = pd.read_csv(f)
      other_unique_players = manager_team_info['player_id'].drop_duplicates().tolist()
      for this_player in other_unique_players:
        if this_player in unique_player_ids:
          unique_player_ids.remove(this_player)
    except:
      print(f"Could not open for id {m_id}")
  
  print(f"{len(unique_player_ids)} unique players")
  mapped = list(filter(lambda p: p['id'] in unique_player_ids, bootstrap_elements))
  mapped_names = list(map(lambda p: p['web_name'], mapped))
  all = team_data[team_data['player_id'].isin(unique_player_ids)]
  points_scoring = all[all['total_points'] > 0].drop_duplicates(subset=['player_id'])
  print(f'{len(points_scoring)} points scoring unique players')
  differential_points = team_data[team_data['player_id'].isin(unique_player_ids)]['total_points'].sum()
  print(f'differentials scored {differential_points} points')

  num_unique_players = len(unique_player_ids)
  unique_player_names = ', '.join(mapped_names)

  return num_unique_players, differential_points, unique_player_names


def generate_files(id):
  print(f"Generate for id {id}")
  data = get_gw_info(id)
  squad_data = get_full_squad_breakdown(id)

#%%
# -====-====-====-====-====-====-====-====-
# Get all global data to use in stats generation
# -====-====-====-====-====-====-====-====-
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
TOTAL_PLAYERS = bootstrap_data['total_players']

h2h_ids = list(map(lambda manager: manager['entry'], h2h_results))
classic_ids = list(map(lambda manager: manager['entry'], classic_reults))
both_league_managers = list(set(h2h_ids) & set(classic_ids))

#%%
for m_id in both_league_managers:
  generate_files(m_id)


# %%
# -====-====-====-====-====-====-====-====-
# Main entry point for stats generation
# -====-====-====-====-====-====-====-====-
for index, player in enumerate(classic_reults):
  id = player['entry']

  if (list(map(lambda p: p['entry'] == id, h2h_results))):
    if (index > 0): break
    name = player['player_name']
    print(f'running for {name}')
    
    team_info = requests.get(f'https://fantasy.premierleague.com/api/entry/{id}/').json()
        
    # Open or create Gameweek info stats
    try:
      f1 = open(get_gw_path(id))
      data = pd.read_csv(f1)
    except:
      print("No file found, generating gw info")
      data = get_gw_info(id)
    
    # Open or create detailed squad info
    try:
      f2 = open(get_team_info_path(id))
      squad_data = pd.read_csv(f2)
    except:
      print("No file found, generating squad data")
      squad_data = get_full_squad_breakdown(id)

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

