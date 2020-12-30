#!/usr/bin/env python3

import re
import pandas as pd
from functools import reduce
from bs4 import BeautifulSoup
from Scripts.Utility.requests import connect
from Scripts.Utility.exceptions import ParseError
from Scripts.Scraper.Soccer.basic import Basic


class MatchReport(Basic):
    score_box = None
    register_teams = None
    events = None
    stats = None
    extra_stats = None

    def __init__(self, url: str):
        super().__init__(key=None, url=url)
        text = connect(url=self.url, return_text=True)
        page_text = text.replace('<!--\n', '')  # replace method used to get tables in comments
        self.soup = BeautifulSoup(page_text, "lxml")
        self.df_tables = pd.read_html(str(self.soup))
        self.register_teams_flag = True if len(self.soup.find_all('div', {'id': "field_wrap"})) > 0 else False

    def to_json(self):
        super().to_json()
        return {
            'URL': self.url,
            'Score Box': self.score_box,
            'Register Teams': self.register_teams,
            'Events': self.events,
            'Stats': self.stats,
            'Extra Stats': self.extra_stats,
            'Dict Tables': self.tables,
        }

    # Parsing
    def set_score_box(self):
        score_box_soup = self.soup.find_all('div', {'class': "scorebox"})[0]
        info_dict = {'DateTime': {}, 'Home Team': {}, 'Away Team': {}, 'Officials': []}
        for i, key in {1: 'Home Team', 3: 'Away Team'}.items():
            temp = score_box_soup.contents[i]
            info_dict[key]['Name'] = temp.contents[1].contents[-2].contents[1].text  # Team name
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
                if len(temp.contents) > location_flag + index:  # in case we don't have manager or captain listed
                    values = temp.contents[location_flag + index].text.split(': ')
                    info_dict[key][values[0]] = self.ascii_name_fix(values[1])

        temp = score_box_soup.contents[5]
        if temp.find('span', {'class': 'venuetime'}) is not None:
            info_dict['DateTime']['Time'] = temp.find('span', {'class': 'venuetime'}).text  # HH:MM as Time of the venue
        info_dict['DateTime']['Date'] = temp.contents[1].contents[0].text  # Day of the week, Month in str, DD, YYYY

        info_dict['Competition'] = temp.contents[2].text  # Competition
        # Officials | Venue | Attendance
        for i in range(3, len(temp.contents)):
            try:
                if ": " in temp.contents[i].text:  # may cause AttributeError
                    values = temp.contents[i].text.split(': ')
                    if values[0] == 'Officials':
                        info_dict[values[0]] = self.get_ref_info(values[1])
                    else:
                        info_dict[values[0]] = values[1]
            except AttributeError:
                continue

        for i, key in {7: 'Home Team', 9: 'Away Team'}.items():
            values = list()
            temp = score_box_soup.contents[i]
            for j in range(1, len(temp.contents), 2):
                temp_values = temp.contents[j]
                values.append({
                    'Type': temp_values.contents[2 if i == 7 else 0].attrs['class'][1],
                    'Player': temp_values.contents[0 if i == 7 else 2].text,
                    'Minute': int(
                        re.search(r'\d+', temp_values.contents[1 if i == 7 else 3]).group())  # 90+2 => 90
                })
            info_dict[key]['Events'] = values

        return info_dict

    def set_register_teams(self):
        register_teams = {'Home Team': {}, 'Away Team': {}}
        if self.register_teams_flag:
            for i, item in {0: 'Home Team', 1: 'Away Team'}.items():
                register_players = {'Starting': [], 'Substitute': []}
                temp_dict = self.df_tables[i].to_dict()  # table 0 and 1 are Home and Away teams register players table
                keys = list(temp_dict.keys())  # first key is the player numbers, second key is the players name
                player_dict = temp_dict[keys[1]]  # getting the names
                player_dict.pop(11)  # removing bench string from the dict at row 11
                for key, player in player_dict.items():
                    flag = 'Starting' if 0 <= key < 11 else 'Substitute'  # separate players on field or on bench
                    register_players[flag].append(self.ascii_name_fix(player))  # adding player name to the list
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

        headers = ['Half Time', 'Full Time', 'Penalty Shootout']
        event_dict = {'First Half': [], 'Half Time': [], 'Full Time': [], 'Penalty Shootout': []}
        events_soup = self.soup.find_all('div', {'id': "events_wrap"})
        if len(events_soup) > 0:
            events_soup = events_soup[0]
            start_index = get_start_index(events_soup.contents[1].contents)
            key = 'First Half'
            for i in range(start_index, len(events_soup.contents[1].contents), 2):
                temp = events_soup.contents[1].contents[i]
                if temp.text in headers:
                    key = headers.pop(0)
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
            order = [1, 2, 0]  # order side for away side
            tmp = re.findall(r'\d+', txt)
            if len(tmp) < 3:  # protection from website bug that don't write 0 in percent column if there was 0 chances
                values = [0, 0, 0]
            else:
                values = [tmp[index] for index in order] if side_flag != 1 else tmp  # re order the list of values
            return {'Successful': values[0], 'Total': values[1], 'Percent': values[2]}

        teams_stats = {'Home Team': {}, 'Away Team': {}}
        stats_soup = self.soup.find_all('div', {'id': "team_stats"})[0].contents[3]
        n = len(stats_soup.contents)
        for i, item in {1: 'Home Team', 3: 'Away Team'}.items():
            teams_stats[item]['Name'] = ' '.join(stats_soup.contents[1].contents[i].contents[0].text.split())
            # getting the stats
            for j in range(3, n - 7, 4):
                key = stats_soup.contents[j].text  # stat name
                temp = stats_soup.contents[j + 2].contents[i].contents[1].contents[1].text  # stat values
                teams_stats[item][key] = temp if j == 3 else stat_to_dict(temp, i)  # store value or separate to dict
            # getting cards count
            teams_stats[item]['Cards'] = {'Yellow': 0, 'Red': 0}
            temp = stats_soup.contents[n - 2].contents[i].contents[1].contents[1].contents[0]
            for j in range(0, len(temp)):
                value = 'Yellow' if temp.contents[j].attrs['class'][0] == 'yellow_card' else 'Red'
                teams_stats[item]['Cards'][value] += 1
        return teams_stats

    def set_extra_stats(self):
        home_dict, away_dict = dict(), dict()
        extra_stats_soup = self.soup.find_all('div', {'id': "team_stats_extra"})
        if len(extra_stats_soup) > 0:
            temp_vars = ['', 'stat', '']
            extra_stats_soup = extra_stats_soup[0]
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
        if len(self.df_tables) == 20:
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
        elif 4 < len(self.df_tables) < 8:  # Minor league with less info
            return {'Home Team': {
                'Players stats': self.set_players_stats(self.df_tables[-4]),
                'Goalkeeper stats': self.set_goalkeeper_stats(self.df_tables[-3]),
            },
                'Away Team': {
                    'Players stats': self.set_players_stats(self.df_tables[-2]),
                    'Goalkeeper stats': self.set_goalkeeper_stats(self.df_tables[-1]),
                }}
        elif 1 < len(self.df_tables) < 5:  # old fixture with less info
            return {'Home Team': {'Players stats': self.set_players_stats(self.df_tables[-2])},
                    'Away Team': {'Players stats': self.set_players_stats(self.df_tables[-1])}
                    }

    def get_ref_info(self, values):  # Officials
        temp = list()
        if len(values) > 0:
            for ref in values.split('\xa0· '):
                info = ref.split(' ')  # split between Name and Position
                temp.append({
                    'Name': self.ascii_name_fix(info[0]),  # Officials Name
                    'Position': info[1].replace('(', '').replace(')', '')  # removing braces from Position
                })
        return temp

    def set_players_stats(self, tables):
        # combine tables and removing duplicate columns
        combine_table = reduce(lambda left, right: pd.merge(left, right), tables) if type(tables) is list else tables
        combine_table = self.change_col_name(combine_table)
        combine_table = self.change_nan(combine_table)
        return {
            'Total': combine_table.iloc[-1].to_json(),
            'Players': [combine_table.iloc[i].to_json() for i in range(len(combine_table[:-1]))]
        }

    def set_goalkeeper_stats(self, table):
        table = self.change_col_name(table)
        table = self.change_nan(table)
        return table.to_json()

    def set_shots_stats(self, table):
        # Rename bad columns
        table = self.change_col_name(table)
        table = table.dropna(thresh=1).reset_index(drop=True)
        table = self.change_nan(table)
        return [table.iloc[i].to_json() for i in range(len(table))]

    def parse(self):
        try:
            self.score_box = self.set_score_box()
            self.register_teams = self.set_register_teams()
            self.events = self.set_events()
            self.stats = self.set_stats()
            self.extra_stats = self.set_extra_stats()
            self.tables = self.set_tables()
        except IndexError:
            raise ParseError(self.url)
        except AttributeError:
            raise ParseError(self.url)
