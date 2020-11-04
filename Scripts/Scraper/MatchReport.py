#!/usr/bin/env python3

import re
import json
import requests
import pandas as pd
from functools import reduce
from bs4 import BeautifulSoup
from Scripts.Utility.json import NpEncoder
from Scripts.Utility.Exceptions import PageNotLoaded, ParseError


class MatchReport:
    score_box = None
    register_teams = None
    events = None
    stats = None
    extra_stats = None
    dict_tables = None

    def __init__(self, link: str, soup: BeautifulSoup = None):
        if soup is None:
            r = requests.get(link)
            if r.status_code != 200:
                raise PageNotLoaded(r.url, r.status_code)
            page_text = r.text.replace('<!--\n', '')
            self.soup = BeautifulSoup(page_text, "lxml")
        else:
            self.soup = soup
        self.url = link
        self.df_tables = pd.read_html(str(self.soup))

    def set_score_box(self):
        score_box_soup = self.soup.find_all('div', {'class': "scorebox"})[0]
        info_dict = {'DateTime': {}, 'Home Team': {}, 'Away Team': {}, 'Officials': []}
        for i, key in {1: 'Home Team', 3: 'Away Team'}.items():
            temp = score_box_soup.contents[i]
            info_dict[key]['Name'] = temp.contents[1].contents[3].contents[1].text  # Team name
            info_dict[key]['Goals'] = temp.contents[3].contents[1].text  # Number of goals as str

            # goals expected or penalties
            values = temp.contents[3].contents[2]  # class = type, text = number as str
            if '\n' not in values:
                info_dict[key][values.attrs['class'][0]] = values.text

            # Wins - Draws - Losses Record
            if '\n' not in temp.contents[4]:
                values = temp.contents[4].text.split('-')
                info_dict[key]['W_D_L'] = {'Wins': values[0], 'Draws': values[1], 'Losses': values[2]}
                location_flag = 4
            else:
                location_flag = 3

            # Managers and Captains
            for index in [4, 6]:  # true location is the location_flag + index
                values = temp.contents[location_flag + index].text.split(': ')
                info_dict[key][values[0]] = values[1].replace('\xa0', ' ')

        temp = score_box_soup.contents[5]
        info_dict['DateTime'] = {
            'Date': temp.contents[1].contents[0].text,  # Day of the week, Month in str, DD, YYYY
            'Time': temp.contents[1].contents[2].text  # HH:MM as Time of the venue
        }
        info_dict['Competition'] = temp.contents[2].text  # Competition
        info_dict['Venue'] = temp.contents[4].text.split(': ')[1]  # Venue

        # Officials
        for ref in temp.contents[5].text.split(': ')[1].split('\xa0· '):
            values = ref.split(' ')  # split between Name and Position
            info_dict['Officials'].append({
                'Name': values[0].replace('\xa0', ' '),  # Officials Name
                'Position': values[1].replace('(', '').replace(')', '')  # removing braces from Position
            })

        for i, key in {7: 'Home Team', 9: 'Away Team'}.items():
            values = list()
            temp = score_box_soup.contents[i]
            for j in range(1, len(temp.contents), 2):
                temp_values = temp.contents[j]
                values.append({
                    'Event': temp_values.contents[2 if i == 7 else 0].attrs['class'][1],
                    'Player': temp_values.contents[0 if i == 7 else 2].text,
                    'Minute': int(
                        re.search(r'\d+', temp_values.contents[1 if i == 7 else 3]).group())
                })
            info_dict[key]['Events'] = values

        return info_dict

    def set_register_teams(self):
        register_teams = {'Home Team': {}, 'Away Team': {}}
        for i, item in {0: 'Home Team', 1: 'Away Team'}.items():
            register_players = {'Starting': [], 'Substitute': []}
            temp_dict = self.df_tables[i].to_dict()  # table 0# and 1# are Home and Away teams register players table
            keys = list(temp_dict.keys())  # first key is the player numbers, second key is the players name
            player_dict = temp_dict[keys[1]]  # getting the names
            player_dict.pop(11)  # removing bench string from the dict at row 11
            for key, player in player_dict.items():
                flag = 'Starting' if 0 <= key < 11 else 'Substitute'  # separate players on field or on bench
                register_players[flag].append(player)  # adding player name to the list
            register_teams[item] = register_players  # placing player list on the dict
        return register_teams

    def set_events(self):
        # get events starting index
        def get_start_index(soup):
            for index in range(len(soup)):
                try:
                    if soup[index].text == 'Kick Off':
                        return index + 2
                except AttributeError:  # first line don't have text attribute
                    continue

        events_soup = self.soup.find_all('div', {'id': "events_wrap"})[0]
        headers = ['Half Time', 'Full Time', 'Penalty Shootout']
        event_dict = {'First Half': [], 'Half Time': [], 'Full Time': [], 'Penalty Shootout': []}
        start_index = get_start_index(events_soup.contents[1].contents)
        key = 'First Half'
        for i in range(start_index, len(events_soup.contents[1].contents), 2):
            temp = events_soup.contents[1].contents[i]
            if temp.text in headers:
                key = headers.pop(0)
                continue
            else:
                time_value = re.findall(r'\d+', temp.contents[1].contents[0])
                event_dict[key].append({
                    'Minute': time_value[0] if len(time_value) == 1
                    else {'Minute': time_value[0], 'Added Time': time_value[1]},
                    'Scoreboard': temp.contents[1].contents[2].text,
                    'Event': temp.contents[3].contents[1].attrs['class'][1],
                    'Player': temp.contents[3].contents[3].contents[1].contents[1].text
                })

        return event_dict

    def set_stats(self):
        # reorder stats per side
        def stat_to_dict(txt, side_flag):
            order = [1, 2, 0]
            tmp = re.findall(r'\d+', txt)
            values = [tmp[index] for index in order] if side_flag != 1 else tmp
            return {'Successful': values[0], 'Total': values[1], 'Percent': values[2]}

        teams_stats = {'Home Team': {}, 'Away Team': {}}
        stats_soup = self.soup.find_all('div', {'id': "team_stats"})[0].contents[3]
        for i, item in {1: 'Home Team', 3: 'Away Team'}.items():
            teams_stats[item]['Name'] = ' '.join(stats_soup.contents[1].contents[i].contents[0].text.split())
            # getting the stats
            for j in range(3, 16, 4):
                key = stats_soup.contents[j].text  # stat name
                temp = stats_soup.contents[j + 2].contents[i].contents[1].contents[1].text  # stat values
                teams_stats[item][key] = temp if j == 3 else stat_to_dict(temp, i)  # store value or separate to dict
            # getting cards count
            teams_stats[item]['Cards'] = {'Yellow': 0, 'Red': 0}
            temp = stats_soup.contents[21].contents[i].contents[1].contents[1].contents[0]
            for j in range(0, len(temp)):
                value = 'Yellow' if temp.contents[j].attrs['class'][0] == 'yellow_card' else 'Red'
                teams_stats[item]['Cards'][value] += 1
        return teams_stats

    def set_extra_stats(self):
        extra_stats_soup = self.soup.find_all('div', {'id': "team_stats_extra"})[0]
        home_dict, away_dict = dict(), dict()
        temp_vars = ['', 'stat', '']
        for j in range(1, len(extra_stats_soup.contents), 2):
            extra_stats_col = extra_stats_soup.contents[j].contents
            for i in range(1, len(extra_stats_col)):
                if i % 4 == 0:  # saving values
                    home_dict[temp_vars[1]] = temp_vars[0]
                    away_dict[temp_vars[1]] = temp_vars[2]
                else:  # extracting values
                    value = extra_stats_col[i].text
                    temp_vars[(i % 4) - 1] = 'Name' if value == '\xa0' else value
        return {'Home Team': home_dict, 'Away Team': away_dict}

    def set_tables(self):
        # Major league with more info
        if len(self.df_tables) in [20]:
            return {'Home Team': {
                'Players stats': self.set_players_stats(self.df_tables[3:9]),
                'Goalkeeper stats': self.set_goalkeeper_stats(self.df_tables[9]),
                'Shots stats': self.set_shots_stats(self.df_tables[-2])
            },
                'Away Team': {
                    'Players stats': self.set_players_stats(self.df_tables[10:16]),
                    'Goalkeeper stats': self.set_goalkeeper_stats(self.df_tables[16]),
                    'Shots stats': self.set_shots_stats(self.df_tables[-1])
            }}
        else:  # Minor league with less info
            return {'Home Team': {
                'Players stats': self.set_players_stats(self.df_tables[3]),
                'Goalkeeper stats': self.set_goalkeeper_stats(self.df_tables[4]),
                'Shots stats': {}
            },
                'Away Team': {
                    'Players stats': self.set_players_stats(self.df_tables[5]),
                    'Goalkeeper stats': self.set_goalkeeper_stats(self.df_tables[6]),
                    'Shots stats': {}
                }}

    @staticmethod
    def change_nan(table):
        return table.where(pd.notnull(table), None)  # Nan to None

    @staticmethod
    def change_col_name(cols):
        # Given better col name
        return [f"{'General' if 'Unnamed' in col[0] else col[0]} - {col[1]}" for col in cols]

    def set_players_stats(self, tables):
        # combine tables and removing duplicate columns
        combine_table = reduce(lambda left, right: pd.merge(left, right), tables) if type(tables) is list else tables
        combine_table.columns = self.change_col_name(combine_table.columns)
        combine_table = self.change_nan(combine_table)
        return {
            'Total': combine_table.iloc[-1].to_dict(),
            'Players': [combine_table.iloc[i].to_dict() for i in range(len(combine_table[:-1]))]
        }

    def set_goalkeeper_stats(self, table):
        table.columns = self.change_col_name(table.columns)
        table = self.change_nan(table)
        return table.to_dict()

    def set_shots_stats(self, table):
        # Rename bad columns
        table.columns = self.change_col_name(table.columns)
        table = table.dropna(thresh=1).reset_index(drop=True)
        table = self.change_nan(table)
        return [table.iloc[i].to_dict() for i in range(len(table))]

    def parse(self):
        try:
            self.score_box = self.set_score_box()
            self.register_teams = self.set_register_teams()
            self.events = self.set_events()
            self.stats = self.set_stats()
            self.extra_stats = self.set_extra_stats()
            self.dict_tables = self.set_tables()
        except IndexError:
            raise ParseError(self.url)
        except AttributeError:
            raise ParseError(self.url)

    def get_score_box(self):
        return self.score_box

    def get_register_teams(self):
        return self.register_teams

    def get_events(self):
        return self.events

    def get_stats(self):
        return self.stats

    def get_extra_stats(self):
        return self.extra_stats

    def get_dict_tables(self):
        return self.dict_tables

    def to_json(self, name: str, file: bool = False):
        data = {
            'URL': self.url,
            'Score Box': self.get_score_box(),
            'Register Teams': self.get_register_teams(),
            'Events': self.get_events(),
            'Stats': self.get_stats(),
            'Extra Stats': self.get_extra_stats(),
            'Dict Tables': self.get_dict_tables(),
        }
        if file:
            # File output
            with open(name, 'w') as outfile:
                json.dump(data, outfile, indent=4, ensure_ascii=True, cls=NpEncoder)
        else:
            return data

    def save_soup(self, name: str):
        data = {
            'Soup String': self.soup.__str__(), # takes 4 times more of spaces
        }
        with open(name, 'w') as outfile:
            json.dump(data, outfile, indent=4, ensure_ascii=False, cls=NpEncoder)
