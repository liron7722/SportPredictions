#!/usr/bin/env python3

import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from ..Utility.Exceptions import PageNotLoaded


class MatchReport:
    def __init__(self, link):
        r = requests.get(link)
        if r.status_code != 200:
            raise PageNotLoaded(r.url, r.status_code)
        page_text = r.text.replace('<!--\n', '')
        self.soup = BeautifulSoup(page_text, "lxml")
        self.tables = pd.read_html(str(self.soup))
        self.score_box = self.get_score_box()
        self.register_teams = self.get_register_teams()
        self.events = self.get_events()
        self.stats = self.get_stats()
        self.extra_stats = self.get_extra_stats()

    def get_score_box(self):
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

    def get_register_teams(self):
        register_teams = {'Home Team': {}, 'Away Team': {}}
        for i, item in {0: 'Home Team', 1: 'Away Team'}.items():
            register_players = {'Starting': [], 'Substitute': []}
            temp_dict = self.tables[i].to_dict()  # table 0# and 1# are Home and Away teams register players table
            keys = list(temp_dict.keys())  # first key is the player numbers, second key is the players name
            player_dict = temp_dict[keys[1]]  # getting the names
            player_dict.pop(11)  # removing bench string from the dict at row 11
            for key, player in player_dict.items():
                flag = 'Starting' if 0 <= key < 11 else 'Substitute'  # separate players on field or on bench
                register_players[flag].append(player)  # adding player name to the list
            register_teams[item] = register_players  # placing player list on the dict
        return register_teams

    def get_events(self):
        # get events starting index
        def get_start_index(soup):
            for index in range(len(soup)):
                try:
                    if soup[index].text == 'Kick Off':
                        return index + 2
                except AttributeError:  # first line don't have text attribute
                    continue

        events_soup = self.soup.find_all('div', {'id': "events_wrap"})[0]
        event_dict = {'First Half': [], 'Second Half': []}
        start_index = get_start_index(events_soup.contents[1].contents)
        for key in event_dict:
            for i in range(start_index, len(events_soup.contents[1].contents), 2):
                temp = events_soup.contents[1].contents[i]
                if temp.text != 'Half Time':
                    event_dict[key].append({
                        'Scoreboard': temp.contents[1].contents[2].text,
                        'Event': temp.contents[3].contents[1].attrs['class'][1],
                        'Player': temp.contents[3].contents[3].contents[1].contents[1].text
                    })
                else:
                    break
        return event_dict

    def get_stats(self):
        def stat_to_dict(txt, side_flag):
            order = [1, 2, 0]
            tmp = re.findall(r'\d+', txt)
            values = [tmp[index] for index in order] if side_flag != 1 else tmp
            return {'Successful': values[0], 'Total': values[1], 'Percent': values[2]}

        teams_stats = {'Home Team': {}, 'Away Team': {}}
        stats_soup = self.soup.find_all('div', {'id': "team_stats"})[0].contents[3]
        for i, item in {1: 'Home Team', 3: 'Away Team'}.items():
            teams_stats[item]['Name'] = ' '.join(stats_soup.contents[1].contents[i].contents[0].text.split())
            for j in range(3, 16, 4):
                key = stats_soup.contents[j].text
                temp = stats_soup.contents[j + 2].contents[i].contents[1].contents[1].text
                teams_stats[item][key] = temp if j == 3 else stat_to_dict(temp, i)
            teams_stats[item]['Cards'] = {'Yellow': 0, 'Red': 0}
            temp = stats_soup.contents[21].contents[i].contents[1].contents[1].contents[0]
            for j in range(0, len(temp)):
                value = 'Yellow' if temp.contents[j].attrs['class'][0] == 'yellow_card' else 'Red'
                teams_stats[item]['Cards'][value] += 1
        return teams_stats

    def get_extra_stats(self):
        extra_stats_soup = self.soup.find_all('div', {'id': "team_stats_extra"})[0]
        home_dict, away_dict = dict(), dict()
        stat_name, home_value, away_value = 'stat', '', ''

        for j in range(1, len(extra_stats_soup.contents), 2):
            extra_stats_col = extra_stats_soup.contents[j].contents
            for i in range(1, len(extra_stats_col)):
                extra_stats_row = extra_stats_col[i]
                if i % 4 == 0:
                    home_dict[stat_name] = home_value
                    away_dict[stat_name] = away_value
                    continue
                else:
                    value = extra_stats_row.text

                    if i % 4 == 1:
                        home_value = value
                    elif i % 4 == 2:
                        value = 'Name' if value == '\xa0' else value
                        stat_name = value
                    elif i % 4 == 3:
                        away_value = value
        return {'Home Team': home_dict, 'Away Team': away_dict}
