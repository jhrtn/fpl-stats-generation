#%%
import csv, pandas

def check_position(pos):
  pos_string = str(pos)
  last_char = pos_string[-1]
  print('checking ' + last_char)
  if (last_char == '1'):
    return pos_string + 'st'
  elif (last_char == '2'):
    return pos_string + 'nd'
  elif (last_char == '3'):
    return pos_string + 'rd'
  else:
    return pos_string + 'th'

def check_position_percentage(pos, num_players):
  pos_perct = (int(pos) / num_players) * 100
  pos_perct = round(pos_perct, 2)
  return str(pos_perct) + "%"

def get_h2h_beat_by_line(h2h_beat_by_most_names, h2h_beat_by_most_num):
  if (h2h_beat_by_most_num <= 1): return ""
  return f"Your h2h nemesis was {h2h_beat_by_most_names} who beat you {h2h_beat_by_most_num} times."

def get_h2h_beat_line(h2h_beat_most_names, h2h_beat_most_num):
  if (h2h_beat_most_num <= 1): return ""
  return f"You were dominating {h2h_beat_most_names} who you beat {h2h_beat_most_num} times."

def get_chips_line(j):
  no_chips = j['num_chips_played'] == 0
  played_wc = j['avg_points_after_wildcard'] > 0
  if no_chips: return ""
  l = f"This season you played {j['num_chips_played']} of {num_chips} chips, with the first being your {j['first_chip']} in GW{j['first_chip_gw']}."
  if not played_wc: return l
  wc_l = f"In the three gameweeks before playing your wildcard you averaged {j['avg_points_before_wildcard']} points, and in the three weeks after, {j['avg_points_after_wildcard']} points. That's a percentage difference of {round(((j['avg_points_after_wildcard'] - j['avg_points_before_wildcard']) / j['avg_points_before_wildcard']) * 100, 2)}%."
  return f"{l} {wc_l}"
  

def insert_congratulation(score):
  score = int(score)
  print('is ' + str(score) + ' bigger than ' + str(league_avg) + '?')
  if (score > league_avg):
    return "Well done for being ahead of the curve!"
  elif (score == league_avg):
    return "You were right on the dot!"
  elif (score < league_avg):
    return "You were trailing just behind."

data = pandas.read_csv(f)
manager_text = []


# %%
league_avg_dreamteam_apps = data['total_apps_in_dreamteam'].mean()
league_avg = data['avg_gw_score'].mean()
league_name = data['classic_league_name'][0]
h2h_name = data['h2h_league_name'][0]
total_players = 9167407
num_chips = 6 #this is usually 5, extra free hit this season

for i, j in data.iterrows():
  # if (i > 0): break
  diff_to_gw_avg = round((j['avg_gw_score'] - league_avg) / abs(league_avg) * 100, 1)
  more_or_less = "more" if diff_to_gw_avg >= 0 else "less"
  diff_to_avg_dreamteam_apps = round((j['total_apps_in_dreamteam'] - league_avg_dreamteam_apps) / league_avg_dreamteam_apps * 100, 1)
  more_or_less_dreamteam = "more" if diff_to_avg_dreamteam_apps >= 0 else "less"
  perct_h2h_won = round(j['h2h_win'] / 38 * 100, 1)
  diff_from_last_season = j['total_score'] - j['points_last_season']
  increase_or_decrease = "increase" if diff_from_last_season > 0 else "decrease"
  best_gw_rank_league_pos = data.sort_values('best_gw_rank', ignore_index=True)
  bst_gw_rank_league  = best_gw_rank_league_pos[best_gw_rank_league_pos['best_gw_rank']==j['best_gw_rank']].index.item() + 1
  
  print(j['manager'])
  # if j['manager'] != 'Joseph Horton':
  #   break
  para_one = f"You finished with a total score of {j['total_score']}. That's a {abs(diff_from_last_season)} point {increase_or_decrease} from last season. Your average gameweek score was {j['avg_gw_score']}, {diff_to_gw_avg}% {more_or_less} than the {league_name} average of {round(league_avg, 1)}. During the season, your best overall rank was {j['best_rank']:,}, this occurred during GW{j['best_rank_gw']}. Your best GW rank was {j['best_gw_rank']:,} in GW{j['best_gw_rank_gw']} when you scored {j['best_gw_rank_score']}. This was the {check_position(bst_gw_rank_league)} best GW rank in your league."

  para_two = f"Your best rank in {league_name} was {check_position(j['league_best_rank'])} where you stood for {j['league_best_rank_duration']} gameweeks. Your worst was {check_position(j['league_worst_rank'])} which lasted for {j['league_worst_rank_duration']} gameweeks."
  
  para_three = f"You made {j['transfer_count']} transfers in total, taking a hit of -{j['transfer_hit']} points along the way. Your players netted you {j['total_num_red_cards']} red cards and {j['total_num_yellow_cards']} yellow cards over the course of the season. Players in your squad appeared in the dream team {j['total_apps_in_dreamteam']} times. That's {diff_to_avg_dreamteam_apps}% {more_or_less_dreamteam} than the {league_name} average."
  
  para_four = f"You captained {j['most_captained_players']} the most, giving them the armband {j['num_times_captained']} times of the 38 gameweeks. Across the whole season you scored {j['points_from_captain']} points from your captain picks, {j['percentage_captain_points']}% of your total points. You selected {j['num_unique_players']} players who no one else in {league_name} picked: {j['unique_players']}. They provided {round(j['points_scored_from_unique_players'] / j['total_score'] * 100, 1)}% of your total score."
  
  para_five = f"{j['num_players_played']} different players appeared in your squad across the season. Your most selected players were {j['top_3_players']} who appeared in your squad {j['top_3_player_apps']} times respectively."
  
  para_six = f"Your best run in {h2h_name} was {j['longest_h2h_winning_streak']} wins in a row, your worst was {j['longest_h2h_losing_streak']} back to back losses. Over the course of the whole season you won {perct_h2h_won}% of your head to matches. {get_h2h_beat_by_line(j['h2h_beat_by_most_names'], j['h2h_beat_by_most_num'])} {get_h2h_beat_line(j['h2h_beat_most_names'], j['h2h_beat_most_num'])}"
  
  para_seven = get_chips_line(j)

  para_eight = f"You missed out on {j['points_on_bench']} points from your benched players. This peaked in gameweek {j['points_on_bench_max_gw']} when there were {j['points_on_bench_max']} points on your bench. You were hoarding cash in GW{j['most_cash_banked_gw']} when you had {j['most_cash_banked_formatted']} in the bank. Your squad value peaked in GW{j['max_team_value_gw']} when it was worth {j['max_team_value_formatted']}."
  
  to_push = {
    "manager": j['manager'].split(' ')[0],
    "para_one": para_one,
    "para_two": para_two,
    "para_three": para_three,
    "para_four": para_four,
    "para_five": para_five,
    "para_six": para_six,
    "para_seven": para_seven,
    "para_eight": para_eight,
    "team_name": j['team_name'],
    "final_main_league_rank": j['final_main_league_rank'],
    "final_overall_rank": "{:,}".format(j['final_overall_rank']),
    "total_score": j['total_score'],
    "final_h2h_league_rank": j['final_h2h_league_rank'],
    "h2h_wld": j['h2h_wld'],
    "rank_perct": j['global_rank_percentage'],
    'h2h_entrants': j['num_h2h_entrants'],
    "classic_entrants": j['num_classic_entrants'],
    "title": f"{j['manager'].split(' ')[0]}, your season in stats"
    }
  manager_text.append(to_push)
  manager_text_df = pandas.DataFrame.from_dict(manager_text)
  # TODO: insert league ID programmatically
