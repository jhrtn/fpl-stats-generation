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
    os.makedirs(BASE_DIR)
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

def get_full_squad_breakdown(player_id, name):
  teams = bootstrap_data['teams']
  gw = 1
  df = pd.DataFrame()
  while gw <= 38:
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
        'web_name': player_detail['web_name']
      }
      df = df.append(played_players_list, ignore_index=True)
    gw += 1
  
  
  if not (os.path.exists(BASE_DIR)):
    os.makedirs(BASE_DIR)
  full_path = os.path.join(BASE_DIR, str(player_id) + TEAM_INFO_EXT)
  df.to_csv(full_path, index=False)

  return df

def get_gw_path(id): return f'{BASE_DIR}/{id}{GW_INFO_EXT}'
def get_team_info_path(id): return f'{BASE_DIR}/{id}{TEAM_INFO_EXT}'

def get_chip_info(gw_data):
  only_chip_weeks = 0
  wildcard_data = {
    'avg_before_wildcard': None,
    'avg_after_wildcard': None,
    'diff': None,
    'perct_change': None
  }
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

  return only_chip_weeks, first_chip, first_chip_gw, chip_type, last_chip, last_chip_gw, last_chip_type, wildcard_data
  
def get_captain_info(team_data):
  cap_points_zip = list(zip(team_data[team_data['is_captain'] == True]['total_points'], team_data[team_data['is_captain'] == True]['points_multiplier']))
  captain_points = sum(list(map(lambda p: p[0] * p[1], cap_points_zip)))
  
  captains = team_data[team_data['is_captain'] == True]
  most_picked_captain_id = captains['player_id'].value_counts().index[0]
  num_times_picked = captains['player_id'].value_counts().tolist()[0]
  most_picked_captain = list(filter(lambda p: p['id'] == most_picked_captain_id, bootstrap_elements))[0]['web_name']
  return most_picked_captain, num_times_picked, captain_points

def get_unique_squad(id, squad_data, manager_ids):
  m_players = squad_data['web_name'].drop_duplicates()
  other_manager_players = []
  to_loop = manager_ids[:]
  print(to_loop)
  if id in to_loop:
    print('removing self from manager list')
    to_loop.remove(id)
  
  for m_id in to_loop:
    time.sleep(0.2)
    try:
      path = os.path.abspath(get_team_info_path(m_id))
      f = open(path)
      others = pd.read_csv(f)['web_name'].drop_duplicates().tolist()
      try:
        other_manager_players.append(others)
      except BaseException as err:
        print(err)
    except:
      print(f"Could not open for id {m_id}")
  flat_data = pd.Series(sum(list(other_manager_players), [])).drop_duplicates()
  unique_squad = []
  for x in m_players:
    if x not in flat_data.values:
      unique_squad.append(x)
  print(unique_squad)
  print(len(unique_squad))
  all = squad_data[squad_data['web_name'].isin(unique_squad)]
  differential_points = all['total_points'].sum()
  return unique_squad, differential_points

def generate_files(id, name):
  print(f"Generate for id {id}")
  data = get_gw_info(id)
  squad_data = get_full_squad_breakdown(id, name)

def get_h2h_data(league_id):
  gw = 1
  results = []#pd.DataFrame()
  
  while gw <= 38:
    print(f"fetching h2h gw {gw}")
    time.sleep(1)
    url = f'https://fantasy.premierleague.com/api/leagues-h2h-matches/league/{league_id}/?event={gw}'
    gw_results = requests.get(url).json()
    
    h2h_res = []
    for result in gw_results['results']:
      p1_score = result['entry_1_points']
      p2_score = result['entry_2_points']
      was_draw = p1_score == p2_score
      p1_name = result['entry_1_player_name']
      p2_name = result['entry_2_player_name']
      p1_id = result['entry_1_entry']
      p2_id = result['entry_2_entry']

      if not was_draw:
        p1_won = True if p1_score > p2_score else False
        

      h2h_res.append({
        'id': result['entry_1_entry'],
        'points': result['entry_1_points'],
        'win': result['entry_1_win'],
        'loss': result['entry_1_loss'],
        'draw': result['entry_1_draw'],
        'total_points': result['entry_1_total'],
        'is_bye': result['is_bye'],
        'is_knockout': result['is_knockout'],
        'gw': gw,
        'beaten_by': p2_name if not p1_won else None,
        'beaten_by_id': p2_id if not p1_won else None,
        'beat': p2_name if p1_won else None,
        'beat_id': p2_id if p1_won else None
      })

      h2h_res.append({
        'id': result['entry_2_entry'],
        'points': result['entry_2_points'],
        'win': result['entry_2_win'],
        'loss': result['entry_2_loss'],
        'draw': result['entry_2_draw'],
        'total_points': result['entry_2_total'],
        'is_bye': result['is_bye'],
        'is_knockout': result['is_knockout'],
        'gw': gw,
        'beaten_by': p1_name if p1_won else None,
        'beaten_by_id': p1_id if p1_won else None,
        'beat': p1_name if not p1_won else None,
        'beat_id': p1_id if not p1_won else None
      })
    
    results.append(
      h2h_res
    )

    gw += 1
  
  return results

def get_h2h_streaks(h2h_res):
  h2h_res = h2h_res.sort_values(['gw']) 
  h2h_res['won'] = (h2h_res['win'] == 1).astype(bool)
  h2h_res['lost'] = (h2h_res['loss'] == 1).astype(bool)
  w = h2h_res.won.astype(bool)
  l = h2h_res.lost.astype(bool)
  h2h_res['streak'] = (w.groupby([w, (~w).cumsum().where(w)]).cumcount().add(1).mul(w))
  h2h_res['l_streak'] = (l.groupby([l, (~l).cumsum().where(l)]).cumcount().add(1).mul(l))
  longest_streak_ends_gw = h2h_res[h2h_res['streak'] == h2h_res['streak'].max()]
  run_length = longest_streak_ends_gw['streak'].values[0]
  end_gw = longest_streak_ends_gw['gw'].values[0]
  start_gw = end_gw - run_length + 1
  longest_l_streak_ends_gw = h2h_res[h2h_res['l_streak'] == h2h_res['l_streak'].max()]
  l_run_length = longest_l_streak_ends_gw['l_streak'].values[0]
  l_end_gw = longest_l_streak_ends_gw['gw'].values[0]
  l_start_gw = l_end_gw - run_length + 1
  
  return run_length, start_gw, end_gw, l_run_length, l_start_gw, l_end_gw
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
h2h_data = requests.get(h2h_league_url).json()
classic_results = classic_data['standings']['results']
h2h_results = h2h_data['standings']['results']

bootstrap_data = requests.get(bootstrap_url).json()
bootstrap_elements = bootstrap_data['elements']
TOTAL_PLAYERS = bootstrap_data['total_players']

h2h_ids = list(map(lambda manager: manager['entry'], h2h_results))
classic_ids = list(map(lambda manager: manager['entry'], classic_results))
both_league_managers = list(set(h2h_ids) & set(classic_ids))

#%%
for m_id in both_league_managers:
  name = list(filter(lambda m: m['entry'] == m_id, classic_results))[0]['player_name']
  generate_files(m_id, name)


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

    only_chip_weeks, first_chip, first_chip_gw, chip_type, last_chip, last_chip_gw, last_chip_type, wildcard_data = get_chip_info(data)

    most_picked_captain, num_times_picked, captain_points = get_captain_info(squad_data)
    
    num_unique_players, differential_points, unique_player_names = get_unique_squad_players(id, squad_data, both_league_managers)

    
    manager_history = requests.get(f'https://fantasy.premierleague.com/api/entry/{id}/history/#/').json()
    past_leagues = manager_history['past']
    
    # check whether this season has already been added, if so this should be 1
    if len(past_leagues) == 0:
      last_season_points = 0
      last_season_rank = 0
    else:
      # if league hasn't yet been added these should be -1
      # or search by season_name '2020/21'
      last_season_points = past_leagues[-2]['total_points']
      last_season_rank = past_leagues[-2]['rank']

    total_points = team_info['summary_overall_points']

    current = {
      'manager': name,
      'player_id': id,
      'team_name': player['entry_name'],
      'total_score': total_points,
      'final_overall_rank': team_info['summary_overall_rank'],
      'final_main_league_rank': list(filter(lambda league: league['id'] == classic_league_id, team_info['leagues']['classic']))[0]['entry_rank'],
      'final_h2h_league_rank': list(filter(lambda league: league['id'] == h2h_league_id, team_info['leagues']['h2h']))[0]['entry_rank'],
      'best_rank': data['overall_rank'].min(),
      'best_rank_gw': data.loc[data['overall_rank'] == data['overall_rank'].min()]['event'].array[0],
      'transfer_count': data['event_transfers'].sum(),
      'transfer_hit': data['event_transfers_cost'].sum(),
      'most_cash_banked': data['bank'].max(),
      'most_cash_banked_formatted': str(data['bank'].max() / 10) + 'M',
      'most_cash_banked_gw': data.loc[data['bank'] == data['bank'].max()]['event'].iat[0],
      'avg_gw_score': round(total_points / NUM_GAMEWEEKS, 1),
      'points_on_bench': data['points_on_bench'].sum(),
      'points_on_bench_max': data['points_on_bench'].max(),
      'points_on_bench_max_gw': data.loc[data['points_on_bench'] == data['points_on_bench'].max()]['event'].iat[0],
      'avg_points_before_wildcard': wildcard_data['avg_before_wildcard'],
      'avg_points_after_wildcard': wildcard_data['avg_after_wildcard'],
      'best_gw_rank': data['rank'].min(),
      'best_gw_rank_score': data[data['rank'] == data['rank'].min()]['points'].array[0],
      'best_gw_rank_gw': data.loc[data['rank'] == data['rank'].min()]['event'].array[0],
      'cup_run_length': len(team_info['leagues']['cup']['matches']),
      'first_chip': chip_type,
      'first_chip_gw': first_chip_gw,
      'last_chip': last_chip_type,
      'last_chip_gw': last_chip_gw,
      'num_chips_played': len(only_chip_weeks),
      # 'global_rank_percentage': check_position_percentage(data['overall_rank'].iat[37], TOTAL_PLAYERS),
      # h2h_draw
      # h2h_loss
      # h2h_win
      # h2h_wld
      # longest_h2h_winning_streak
      # longest_h2h_winning_streak_end_gw
      # longest_h2h_winning_streak_start_gw
      'max_team_value': data['value'].max(),
      'max_team_value_formatted': str(data['value'].max() / 10) + 'M',
      'max_team_value_gw': data.loc[data['value'] == data['value'].max()]['event'].iat[0],
      'most_captained_player': most_picked_captain,
      'num_times_captained': num_times_picked,
      'points_from_captain': captain_points,
      'percentage_captain_points': round((captain_points / total_points) * 100, 1),
      'num_leagues_entered': len(team_info['leagues']['classic']) + len(team_info['leagues']['h2h']),
      # num_times_h2h_scamp
      # num_times_h2h_unlucky
      'points_per_minute_max': round((total_points / squad_data['minutes'].sum()) * MAX_SQUAD_MINUTES, 3),
      'points_per_minute_played': round(total_points / squad_data['minutes'].sum(), 3),
      'num_unique_players': num_unique_players,
      'points_scored_from_unique_players': differential_points,
      'unique_points_perct_of_total': (differential_points / total_points) * 100,
      'unique_players': unique_player_names,
      'rank_last_season': last_season_rank,
      'points_last_season': last_season_points,
      'percentage_points_change_last_season': round(((total_points - last_season_points) / last_season_points) * 100, 2),
      'total_apps_in_dreamteam': squad_data['in_dreamteam'].sum(),
      'total_minutes_fielded': squad_data['minutes'].sum(),
      'total_num_red_cards': squad_data['red_cards'].sum(),
      'total_num_yellow_cards': squad_data['yellow_cards'].sum(),
      'total_minutes_perct_of_possible': round((squad_data['minutes'].sum() / MAX_SQUAD_MINUTES) * 100, 1),
      'total_score_if_no_hits_taken': total_points + data['event_transfers_cost'].sum(),
      'worst_gw_rank': data['rank'].max(),
      'worst_gw_rank_score': data[data['rank'] == data['rank'].max()]['points'].array[0],
      'worst_gw_rank_gw': data.loc[data['rank'] == data['rank'].max()]['event'].array[0],
    }

    
    # print(gw_info)

    # print(current)
  else:
    print(f"player {player['player_name']} is not in both leagues")

  
  # %%

