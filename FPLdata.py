import pandas as pd
import requests
import numpy as np
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)


# fbref.com table link for 2023-2024 PL season utlized to scrap player 'Standard Stats' data 
url_df = 'https://fbref.com/en/comps/Big5/stats/players/Big-5-European-Leagues-Stats'

# Extract the data at index[0]
FPLdf = pd.read_html(url_df)[0]

# Remove the multi-index conditon of the df and create new headers 
FPLdf.columns = [' '.join(col).strip() for col in FPLdf.columns]
FPLdf = FPLdf.reset_index(drop=True)

# Creating a list to stoere the new column names
new_columns = []
# Iterate throught every column in our df to remove 'level_0' and only extract the string that describe the stat
for col in FPLdf.columns:
  if 'level_0' in col:
      new_col = col.split()[-1] 
  else:
      new_col = col
  new_columns.append(new_col)

# Renames our df columns to those stored in our new list
FPLdf.columns = new_columns
FPLdf = FPLdf.fillna(0)

# Gets the current age of the player
FPLdf['Age'] = FPLdf['Age'].str[:2]
# Player's secondary position
FPLdf['Position_2'] = FPLdf['Pos'].str[3:]
# Player's primary position
FPLdf['Position'] = FPLdf['Pos'].str[:2]
# Cleans strings that beling to Nation and Comp columns
FPLdf['Nation'] = FPLdf['Nation'].str.split(' ').str.get(1)
FPLdf['League'] = FPLdf['Comp'].str.split(' ').str.get(1)
FPLdf['League_'] = FPLdf['Comp'].str.split(' ').str.get(2)
FPLdf['League'] = FPLdf['League'] + ' ' + FPLdf['League_']
# Removes the following columns as they are no longer needed
FPLdf = FPLdf.drop(columns=['League_', 'Comp', 'Rk', 'Pos','Matches'])

# Concats positions to their acronyms 
FPLdf['Position'] = FPLdf['Position'].replace({'MF': 'Midfielder', 'DF': 'Defender', 'FW': 'Forward', 'GK': 'Goalkeeper'})
FPLdf['Position_2'] = FPLdf['Position_2'].replace({'MF': 'Midfielder', 'DF': 'Defender',
                                                 'FW': 'Forward', 'GK': 'Goalkeeper'})
FPLdf['League'] = FPLdf['League'].fillna('Bundesliga')

FPLdf = FPLdf.loc[FPLdf['League'] == 'Premier League' ]
FPLdf['Playing Time Min'] = pd.to_numeric(FPLdf['Playing Time Min'], errors = 'coerce') 

filtered_fbref_df = FPLdf[FPLdf['Playing Time Min'] > 450]

#Reset index to start at 1
filtered_fbref_df = filtered_fbref_df.reset_index(drop=True)
filtered_fbref_df.index = np.arange(1, len(filtered_fbref_df) + 1)

filtered_fbref_df.to_csv("data_fbref.csv")

########################################################### NOW USING THE API FOR STORED FPL DATA ###########################################################
base_url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
historical_data_base_url= 'https://fantasy.premierleague.com/api/element-summary/'

r = requests.get(base_url)
json = r.json()

elements_df = pd.DataFrame(json['elements'])
elements_types_df = pd.DataFrame(json['element_types'])
teams_df = pd.DataFrame(json['teams'])

# Maps column element_type from elements_df to singular_name from elements_types_df which gives us the players' positions.
elements_df['element_type'] = elements_df.element_type.map(elements_types_df.set_index('id').singular_name)
# Maps column team from elements_df to name from teams_df which gives us the teams' names.
elements_df['team'] = elements_df.team.map(teams_df.set_index('id').name)

# Initialize the columns we want to see
player_detail_cols = ['id','first_name','second_name','team','ict_index','total_points','now_cost','value_season']
# Trimmed DF to stats we wanna analayze first
trimmed_elements_df = elements_df.loc[:,['first_name','second_name',\
                                   'id','ict_index',
                                'code',\
                                'team',\
                                'element_type','selected_by_percent','now_cost',\
                                'minutes','transfers_in',\
                                'ict_index_rank', 'ict_index_rank_type',\
                                'value_season','total_points','points_per_game']]

trimmed_elements_df['points_per_minute'] = trimmed_elements_df['total_points']/trimmed_elements_df['minutes']
trimmed_elements_df['matches'] = trimmed_elements_df['minutes']/90
trimmed_elements_df['value_season'] =trimmed_elements_df['value_season'].astype(float)

#print(trimmed_elements_df.sort_values('value_season',ascending=False).head(11)[player_detail_cols])
#print(trimmed_elements_df.sort_values('matches').head())
print(trimmed_elements_df['transfers_in'].astype(float).corr(trimmed_elements_df['total_points']))
filtered_fpl_df = trimmed_elements_df[trimmed_elements_df.minutes > 450]

filtered_fpl_df.to_csv("data_fplAPI.csv")
