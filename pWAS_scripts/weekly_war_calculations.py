#!/usr/bin/Python

# Created by: William P Bone and Christopher J Adams 11/28/2020
# 

###############################################################################
###
### This script calculates WAR given the weekly game results
###
###############################################################################

#import cProfile
import sys
import pandas as pd
import numpy as np
import random
import cProfile
import time
import getopt
import pdb

def help(exit_code = 1):
    print("""-----------------------------------------------------------------
ARGUMENTS
    -g => <csv> starting game week REQUIRED
    -w => <csv> weekly xFpts REQUIRED
    -t => <csv> season-long WAR REQUIRED (If you do not have a file please set this flag to "FALSE")
    -o => <path> rootname of output files (rootname_gameweeks.csv and rootname_season.csv) REQUIRED
""")
    sys.exit(exit_code)
###############################################################################
###########################  COLLECT AND CHECK ARGUMENTS  #####################
###############################################################################


## MAIN ##

def main(argv): 
    pd.set_option('display.max_colwidth', 100)
    try: 
        opts, args = getopt.getopt(sys.argv[1:], "g:w:t:o:")
    except getopt.GetoptError:
        print("Error: Incorrect usage of getopts flags!")
        help() 
    
    options_dict = dict(opts)

    ## Required arguments
    try:
        #game week to start from
        start_gameweek = options_dict['-g']
        #weekly fantrax xFpts file
        weekly_xfpts_csv = options_dict['-w']
        season_long_war_csv = options_dict['-t']
        output_file = options_dict['-o']
    except KeyError:
        print("Error: One of your required arguments does not exist.")
        help()

    ## Optional Arguments
    #minute_requirement = options_dict.get('-m', 60)

    print("Acceptable Inputs Given")

    start_gameweek = int(start_gameweek)

    driver(start_gameweek, weekly_xfpts_csv, season_long_war_csv, output_file)


def driver(start_gameweek, weekly_xfpts_csv, season_long_war_csv, output_file):

    #count the number starter and ww guys for each week and stor here
    starter_counts_F = []
    ww_counts_F = []
    starter_counts_M = []
    ww_counts_M = []
    starter_counts_D = []
    ww_counts_D = []

    #prep the two types of output files
    output_file_weekly = output_file + "_weekly.csv"
    output_file_season = output_file + "_season.csv"


    num_sample = 5000
    #num_sample = 5000

    #if a season war file is provided
    if season_long_war_csv != "False":
        season_input_df = pd.read_csv(season_long_war_csv)

    weekly_xfpts_df = pd.read_csv(weekly_xfpts_csv)

    #output dataframe
    combined_weeks_df = pd.DataFrame(data=None, index=None, columns=['Player','Pos', 'gameweek', 'pWAS', 'ww_pWAS', 'WAR'])

    #find the last game week in the file
    gameweek_col = weekly_xfpts_df["game_week"]
    last_gameweek = gameweek_col.max()
    print("last game week in the provided file is:")
    print(last_gameweek)


    #NOTE make this percent owned
    #fwd_group_dict = {1: 16,
    #                  2: 20,
    #                  3: 24}
    #fwd_group_dict = {1: 97, 
    #                  2: 90, 
    #                  3: 80} 
    fwd_group_dict = {1: 90,
                      2: 80,
                      3: 70}

    #mid_group_dict = {1: 32,
    #                  2: 40,
    #                  3: 48}
    mid_group_dict = {1: 80,
                      2: 70,
                      3: 50}
    #def_group_dict = {1: 32,
    #                  2: 40,
    #                  3: 48}
    def_group_dict = {1: 80,
                      2: 70,
                      3: 50}

    #only starters
    #only include people who played in the anaylsis
    #19_20 data uses "Min.x" instead of "Min_x" 
    weekly_xfpts_df = weekly_xfpts_df.loc[(weekly_xfpts_df['GP'] == 1) & (weekly_xfpts_df['Min_x'] >= 60)]

    # starting with the user supplied game week calculate the week WAR for each week up to the last one
    gameweek = start_gameweek

    while gameweek <= last_gameweek:

        print("game week")
        print(gameweek)
        print("\n\n")

        #only grab data from this gameweek

        gameweek_xfpts_df = weekly_xfpts_df.loc[weekly_xfpts_df['game_week'] == gameweek]

        player_pwas_dict = {}
        player_dict = {}
        for group in list(fwd_group_dict.keys()):

            ## FWDS
            fwd_total_starters = fwd_group_dict[group]
            fwd_starter_game_scores, fwd_ww_game_scores = get_starters_and_ww("F", gameweek_xfpts_df, fwd_total_starters, starter_counts_F, ww_counts_F)
        
            ## MIDS
            mid_total_starters = mid_group_dict[group]
            mid_starter_game_scores, mid_ww_game_scores = get_starters_and_ww("M",  gameweek_xfpts_df, mid_total_starters, starter_counts_M, ww_counts_M)
        
            ## DEF
            def_total_starters = def_group_dict[group]
            def_starter_game_scores, def_ww_game_scores = get_starters_and_ww("D", gameweek_xfpts_df, def_total_starters,starter_counts_D, ww_counts_D)
        
            starter_score_dict = {"D": def_starter_game_scores,
                                  "M": mid_starter_game_scores,
                                  "F": fwd_starter_game_scores}
            ww_score_dict = {"D": def_ww_game_scores,
                             "M": mid_ww_game_scores,
                             "F": fwd_ww_game_scores}
            ### Average Starter team sampling

            starter_avg_game = []
            ww_def_avg_game = []
            ww_mid_avg_game = []
            ww_fwd_avg_game = []
            start = time.time()
    
            formation_list = [[3,4,3], [3,5,2], [4,4,2], [4,3,3]]

            for formation in formation_list:

                def_formation_count, mid_formation_count, fwd_formation_count = formation

                ## first get the average game with all starters
                starter_lineup_avg_game = get_game_results(starter_score_dict, formation, num_sample)
                starter_avg_game = starter_avg_game + starter_lineup_avg_game

                ## Average games for one player missing at each position
                # DEF
                def_missing_formation = formation[:]
                def_missing_formation[0] -= 1
                ww_def_included_avg_game = get_game_results(starter_score_dict, def_missing_formation, num_sample, ww_score_dict['D'])
                ww_def_avg_game = ww_def_avg_game + ww_def_included_avg_game

                # MID
                mid_missing_formation = formation[:]
                mid_missing_formation[1] -= 1
                ww_mid_included_avg_game = get_game_results(starter_score_dict, mid_missing_formation, num_sample, ww_score_dict['M'])
                ww_mid_avg_game = ww_mid_avg_game + ww_mid_included_avg_game

                # FWD
                fwd_missing_formation = formation[:]
                fwd_missing_formation[2] -= 1
                ww_fwd_included_avg_game = get_game_results(starter_score_dict, fwd_missing_formation, num_sample, ww_score_dict['F'])
                ww_fwd_avg_game = ww_fwd_avg_game + ww_fwd_included_avg_game

            # shuffle the avg game data and calculate the ww_pwas values
            random.shuffle(starter_avg_game)

            def_ww_win_percentage = get_win_percentage(ww_def_avg_game, starter_avg_game)
            def_ww_war = def_ww_win_percentage - 0.5
            print('Mean def ww game score: ', np.mean(ww_def_avg_game))
            print('std def ww game score: ', np.std(ww_def_avg_game))
            print("DEF avg war lost: ", def_ww_war)

            mid_ww_win_percentage = get_win_percentage(ww_mid_avg_game, starter_avg_game)
            mid_ww_war = mid_ww_win_percentage - 0.5
            print('Mean mid ww game score: ', np.mean(ww_mid_avg_game))
            print('std mid ww game score: ', np.std(ww_mid_avg_game))
            print("MID avg war lost: ", mid_ww_war)

            fwd_ww_win_percentage = get_win_percentage(ww_fwd_avg_game, starter_avg_game)
            fwd_ww_war = fwd_ww_win_percentage - 0.5
            print('Mean fwd ww game score: ', np.mean(ww_fwd_avg_game))
            print('std fwd ww game score: ', np.std(ww_fwd_avg_game))
            print("FWD avg war lost: ", fwd_ww_war)

            ## Next cycle through each player
            ## For all players SAMPLING procedure
            #player_dict = {}
            print('starting player simulations \n\n')

            print('number of players:')
            print(gameweek_xfpts_df.shape[0])
            for index, row in gameweek_xfpts_df.iterrows():
                #print(index)
            #for row in gameweek_xfpts_df.iterrows():
                #pdb.set_trace()
 
                sim_games = []
                #parse from old WAR file
                #player = row[1]['Player']
                #pos = row[1]['Position']
                player = row['Player']
                pos = row['Position']
                #games = row['n']
                #old_war = row['WAR']
                print(player) 

                #if the player played and played at least 60 minutes add 1 to the games count
                #if gameweek_xfpts_df.loc[(gameweek_xfpts_df['Position'] == pos) & (gameweek_xfpts_df['GP'] == 1) & (gameweek_xfpts_df['Min'] >= 60)]:
                    #games += 1

                    #set GS (game starter) to 1
                    #GS = 1

                #otherwise set GS to 0
                #else:
                    #GS = 0

                #print(player)
                player_weekly_pts = gameweek_xfpts_df.loc[(gameweek_xfpts_df['Player'] == player)]['FPts']
                if player_weekly_pts.empty:
                    print(player + " is missing from weekly pts")
                    continue
            
                for formation in formation_list:
                    def_formation_count, mid_formation_count, fwd_formation_count = formation
                    def_count = def_formation_count
                    mid_count = mid_formation_count
                    fwd_count = fwd_formation_count
                    if pos == 'D':
                        def_count -= 1
                        ww_pwas = def_ww_war
                    elif pos == 'M':
                        mid_count -= 1
                        ww_pwas = mid_ww_war
                    elif pos == 'F':
                        fwd_count -= 1
                        ww_pwas = fwd_ww_war
                
                    def_index_pos = 0
                    mid_index_pos = 0
                    fwd_index_pos = 0

                    player_sample = player_weekly_pts.tolist()
                    def_samples = list(def_starter_game_scores.sample(n=(def_count * num_sample), replace = True))
                    mid_samples = list(mid_starter_game_scores.sample(n=(mid_count * num_sample), replace = True))
                    fwd_samples = list(fwd_starter_game_scores.sample(n=(fwd_count * num_sample), replace = True))


                    for sample in range(num_sample):
                        def_index_2 = def_index_pos + def_count
                        mid_index_2 = mid_index_pos + mid_count
                        fwd_index_2 = fwd_index_pos + fwd_count
                        total_pts = 0
                        def_pts = def_samples[def_index_pos:def_index_2]
                        mid_pts = mid_samples[mid_index_pos:mid_index_2]
                        fwd_pts = fwd_samples[fwd_index_pos:fwd_index_2]
                        #player_sample = player_samples[sample]

                        all_pts = def_pts + mid_pts + fwd_pts + player_sample
                        for pts in all_pts:
                            total_pts += pts

                        def_index_pos = def_index_2
                        mid_index_pos = mid_index_2
                        fwd_index_pos = fwd_index_2

                        sim_games.append(total_pts)

                sim_games_mean = np.mean(sim_games)
                sim_games_sd = np.std(sim_games)
            
                win_percentage = get_win_percentage(sim_games, starter_avg_game)
                pwas = win_percentage - 0.5
                #games_missed = 38 - games

                #pdb.set_trace()
                #try to update the pwas andd ww_pwas
                try:
                   # print(row)
                    player_dict[player][2] += pwas
                    player_dict[player][3] += ww_pwas
                    #print(pwas)
                    #print(ww_pwas)

                #if player isn't in the dictionary add the player
                except KeyError:
                    player_dict[player] = [pos, gameweek, pwas, ww_pwas]
                    #print(player_dict[player])


        ## Finally clean up player dict

        final_player_dict = {}
        for player in player_dict:
            total_groups = len(list(fwd_group_dict.keys()))
            #print(total_groups)
            pos, gameweek, pwas, ww_pwas = player_dict[player]
            print(player_dict[player])
            avg_pwas = pwas / float(total_groups)
            print(avg_pwas)
            avg_ww_pwas = ww_pwas / float(total_groups)
            print(avg_ww_pwas)
            war = avg_pwas - avg_ww_pwas
            # war + avg_pwas when GS =1, war - avg_ww_pwas when GS=0
            #war = war + (GS * avg_pwas) - ( (1 - GS ) * avg_ww_pwas)
            final_player_dict[player] = [pos, \
                                         gameweek, \
                                         avg_pwas, \
                                         avg_ww_pwas, \
                                         war]

        ## convert player dict to pandas df
        week_df = pd.DataFrame.from_dict(final_player_dict, orient='index', columns = ['Pos', 'gameweek', 'pWAS', 'ww_pWAS', 'WAR'])

        week_df = week_df.rename_axis("Player").reset_index()

        #pdb.set_trace()

        #df = df.sort_values(by = 'WAR', ascending = False)
        #add this week's data to combined weeks df
        combined_weeks_df = combined_weeks_df.append(pd.DataFrame(data = week_df))

        gameweek += 1

    #after all weeks run, write the combined_weeks_df to file
    combined_weeks_df = combined_weeks_df.sort_values(by = ['gameweek','WAR'], ascending = [True,False])
    combined_weeks_df.to_csv(output_file_weekly)
    
    #groupby player summary to make the season long file
    #season_df = combined_weeks_df.groupby(['Player']).agg({'WAR':'sum'})
    #these arre the aggregations to perform
    aggregations = {'WAR':{'sum'},'ww_pWAS':{'mean'}, 'pWAS':{'mean'},'gameweek':{'count'}}

    season_df = pd.DataFrame(combined_weeks_df.groupby(['Player','Pos']).agg(aggregations))

    #fix the column names
    season_df.columns = season_df.columns.droplevel(0)
    season_df = season_df.reset_index()    
    season_df.columns = ['Player','Pos','season_WAR', 'avg_ww_pWAS', 'avg_pWAS', 'games_played']

    #if season_long_war_csv was provided add the old data
    if season_long_war_csv != "False":

        #weight the averages by the number games for combining
        season_input_df['avg_ww_pWAS'] = season_input_df['avg_ww_pWAS'] * season_input_df['games_played']
        season_input_df['avg_pWAS'] = season_input_df['avg_pWAS'] * season_input_df['games_played']

        season_df['avg_ww_pWAS'] = season_df['avg_ww_pWAS'] * season_df['games_played']
        season_df['avg_pWAS'] = season_df['avg_pWAS'] * season_df['games_played']

        aggregations = {'season_WAR':{'sum'},'avg_ww_pWAS':{'sum'}, 'avg_pWAS':{'sum'},'games_played':{'sum'}}

        #append the files together
        season_df = season_df.append(pd.DataFrame(data = season_input_df ))
        #combine lines with the same players
        season_df = pd.DataFrame(season_df.groupby(['Player','Pos']).agg(aggregations))

        #fix the column names
        season_df.columns = season_df.columns.droplevel(0)
        season_df = season_df.reset_index()
        season_df.columns = ['Player','Pos','season_WAR', 'avg_ww_pWAS', 'avg_pWAS', 'games_played']

        #divide avg pwas by the number of games so that th
        season_df['avg_ww_pWAS'] = season_df['avg_ww_pWAS'] / season_df['games_played']
        season_df['avg_pWAS'] = season_df['avg_pWAS'] / season_df['games_played']

    #sort by WAR
    season_df = season_df.sort_values(by = ['season_WAR'], ascending = False)

    #write season data to file
    season_df.to_csv(output_file_season)

    #write starter and waiver wire counts to file
    count_dict = {"starter_counts_F": starter_counts_F, "ww_counts_F": ww_counts_F, "starter_counts_M": starter_counts_M, "ww_counts_M": ww_counts_M, "starter_counts_D": starter_counts_D, "ww_counts_D": ww_counts_D }
    count_df = pd.DataFrame(count_dict)
    count_df.to_csv("starter_ww_counts.csv")

#NOTE can edit this to allow for player week result to be added instead of a ww_added_df
def get_game_results(starter_score_dict, pos_counts, num_sample, ww_added_df = None):

    def_count, mid_count, fwd_count = pos_counts

    def_samples = list(starter_score_dict['D'].sample(n=def_count*num_sample, replace = True))
    mid_samples = list(starter_score_dict['M'].sample(n=mid_count*num_sample, replace = True))
    fwd_samples = list(starter_score_dict['F'].sample(n=fwd_count*num_sample, replace = True))
    if ww_added_df is not None:
        ww_samples = list(ww_added_df.sample(n=num_sample, replace = True))

    def_index_pos = 0
    mid_index_pos = 0
    fwd_index_pos = 0

    game_list = []

    for sample in range(num_sample):
        def_index_2 = def_index_pos + def_count
        mid_index_2 = mid_index_pos + mid_count
        fwd_index_2 = fwd_index_pos + fwd_count
        total_pts = 0
        def_pts = def_samples[def_index_pos:def_index_2]
        mid_pts = mid_samples[mid_index_pos:mid_index_2]
        fwd_pts = fwd_samples[fwd_index_pos:fwd_index_2]
        all_pts = def_pts + mid_pts + fwd_pts
        for pts in all_pts:
            total_pts += pts
        if ww_added_df is not None:
            ww_pts = ww_samples[sample]
            total_pts += ww_pts


        def_index_pos = def_index_2
        mid_index_pos = mid_index_2
        fwd_index_pos = fwd_index_2

        game_list.append(total_pts)
    
    return game_list   



def get_starters_and_ww(pos, gameweek_xfpts_df, total_starters, starter_counts, ww_counts):

    #remove the "%" from the % Owned column so we can sort on it
    #pdb.set_trace()
    gameweek_xfpts_df["% Owned"] = gameweek_xfpts_df["% Owned"].astype(str)
    gameweek_xfpts_df["% Owned"] = gameweek_xfpts_df["% Owned"].str.replace(r'%', '')
    gameweek_xfpts_df["% Owned"] = gameweek_xfpts_df["% Owned"].str.replace(r'-', '0')
    gameweek_xfpts_df["% Owned"] = gameweek_xfpts_df["% Owned"].astype(float)

    #remove the "%" from the % Owned change column so we can sort on it
    #gameweek_xfpts_df["+/-"] = gameweek_xfpts_df["+/-"].str.replace(r'%', '')
    #gameweek_xfpts_df["+/-"] = gameweek_xfpts_df["+/-"].str.replace(r'-', '0')
    #gameweek_xfpts_df["+/-"] = gameweek_xfpts_df["+/-"].astype(float)

    #combine the % Owned and % Owned change to be the final % Owned
    Pct_Owned = gameweek_xfpts_df["% Owned"]
    gameweek_xfpts_df["Pct_Owned"] = Pct_Owned

    #pdb.set_trace()
    #number of players that played this position this week
    pos_end = gameweek_xfpts_df.loc[(gameweek_xfpts_df['Position'] == pos)].shape[0]

    starters = list(gameweek_xfpts_df.loc[(gameweek_xfpts_df['Position'] == pos) & (gameweek_xfpts_df["% Owned"] >= total_starters)].sort_values(by = ['Pct_Owned','Rk'], ascending = [False,True])['Player'])
    #starters = list(gameweek_xfpts_df.loc[(gameweek_xfpts_df['Position'] == pos)].sort_values(by = ['Pct_Owned','Rk'], ascending = [False,True])[0:total_starters]['Player'])
    #starters = list(xfpts_df.loc[(xfpts_df['Position'] == pos)].sort_values(by = 'mean_xFpts', ascending = False)[0:total_starters]['Player'])
    num_starters = len(starters)
    starter_counts.append(num_starters)
    print(pos + " starters: \n", starters)
    starter_game_scores = gameweek_xfpts_df.loc[(gameweek_xfpts_df['Player'].isin(starters))]['FPts']

    ww_players = list(gameweek_xfpts_df.loc[(gameweek_xfpts_df['Position'] == pos) & (gameweek_xfpts_df["% Owned"] < total_starters)].sort_values(by = ['Pct_Owned','Rk'], ascending = [False,True])['Player'])
    #ww_players = list(gameweek_xfpts_df.loc[(gameweek_xfpts_df['Position'] == pos)].sort_values(by = ['Pct_Owned','Rk'], ascending = [False,True])[total_starters:pos_end]['Player'])
    #ww_players = list(xfpts_df.loc[(xfpts_df['Position'] == pos)].sort_values(by = 'mean_xFpts', ascending = False)[ww_start:ww_end]['Player'])
    num_ww = len(ww_players)
    ww_counts.append(num_ww)
    print(pos + " ww: \n", ww_players)
    ww_game_scores = gameweek_xfpts_df.loc[(gameweek_xfpts_df['Player'].isin(ww_players))]['FPts']

    return starter_game_scores, ww_game_scores


def get_win_percentage(game_list_1, game_list_2):
    
    num_matchups = len(game_list_1)

    diff = np.array(game_list_1) - np.array(game_list_2)
    
    win_count = 0
    for d in diff:
        if d > 0:
            win_count += 1
    win_percentage = win_count / num_matchups

    return win_percentage


if __name__ == "__main__":
    main(sys.argv[1:])
 
