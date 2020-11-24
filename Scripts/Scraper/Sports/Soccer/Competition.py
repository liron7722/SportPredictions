#!/usr/bin/env python3

import pandas as pd
from bs4 import BeautifulSoup
from Scripts.Utility.json import save
from Scripts.Utility.requests import connect
from Scripts.Utility.Exceptions import PageNotLoaded
from Scripts.Scraper.Sports.Soccer.Season import Season


class Competition:
    base = 'https://fbref.com/'  # main url
    url = None
    logger = None
    tables = None
    db_client = None
    seasons: list = []
    to_scrape: list = []
    scraped_flag: bool = False

    def __init__(self, key, url, logger=None):
        self.key = key
        self.url = url
        self.add_logger(logger=logger)
        self.log(f'Competition Initialize with Key: {key},\tUrl: {url}')
        r_text = connect(url=self.base + self.url)
        page_text = r_text.replace('<!--\n', '')
        self.soup = BeautifulSoup(page_text, "lxml")

    # Setters
    def add_logger(self, logger):
        self.logger = logger

    def load_db(self, data: dict):
        self.log(f'Cmd: load_db')
        if data is None:
            self.log(f'Cmd: Nothing to load')
        else:  # Todo check if make sense
            for season in data:
                if len(season['To Scrape']) > 0:
                    self.add_season(season['URL'], season['Basic Info'], len(self.seasons))

    def add_season(self, url: str, info, index: int):
        self.log(f'Cmd: add_season\t Url: {url}')
        temp = Season(self.key, url, info)
        temp.scrape()
        self.log('Finished scrape the season')
        self.seasons.append({index: temp})

    # Getters
    def get_seasons_as_json(self):
        return [season.to_json() for season in self.seasons]

    def get_tables(self):
        return [[table.iloc[i].to_json() for i in range(len(table))] for table in self.tables]

    # Utility functions
    @staticmethod
    def change_col_name(table):
        # Given better col name
        cols = table.columns
        if type(cols) == pd.core.indexes.multi.MultiIndex:
            table.columns = [f"{'General' if 'Unnamed' in col[0] else col[0]} - {col[1]}" for col in cols]
        return table

    @staticmethod
    def change_nan(table):
        return table.where(pd.notnull(table), None)  # Nan to None

    def parse_general_info(self):
        self.log(f'Cmd: parse_general_info')
        temp = []
        dfs = pd.read_html(str(self.soup))
        for table in dfs:
            table = self.change_col_name(table)
            table = self.change_nan(table)
            temp.append(table)
        self.tables = temp

    def get_history_link(self):
        self.log(f'Cmd: get_history_link')
        temp = self.soup.find_all('ul', {'class': "hoversmooth"})[1]  # navbar html
        # navbar index (history) url
        index_url = temp.find('li', {'class': "index"}).find('a').get('href').removeprefix('/')
        return self.base + index_url

    # Scrape functions
    def scrape_seasons(self, soup: BeautifulSoup, scrape_list: list):
        self.log(f'Cmd: scrape_seasons')
        df = pd.read_html(str(soup))[0]  # get history full table
        urls = soup.find('tbody').find_all('tr')  # get links of all seasons
        scrape_list = [j for j in range(len(urls))] if len(scrape_list) == 0 else scrape_list
        self.log(f'Info: Going to scrape {len(scrape_list)} Seasons')
        for i in scrape_list:
            info = df.iloc[i]  # general information
            if urls[i].contents[0].find('a') is None:  # this row don't have a url
                self.log(f'Skipped row {i} while trying to parse season table')
                continue
            else:
                url = urls[i].contents[0].find('a').get('href')  # Competition url
            try:
                self.add_season(url=url, info=info, index=i)
                self.log(f'Season {i}/{len(scrape_list)} successfully scrape at Url: {url}', level=20)
            except PageNotLoaded:
                self.log(f'Error accord,\tSeason {i}/{len(scrape_list)} failed scrape at Url: {url}')
                if i not in self.to_scrape:  # avoiding duplicate
                    self.to_scrape.append(i)
        self.scraped_flag = True

    def scrape(self):
        self.log(f'Cmd: scrape\t'
                 f'Key: {self.key}\t'
                 f'Url: {self.url}')
        link = self.get_history_link()
        # check if current position is the history url
        soup = BeautifulSoup(connect(link), "lxml")
        self.scrape_seasons(soup, self.to_scrape)  # Starting call scrape for each season
        self.is_scraped()  # Going throw all season check who didn't scrape

    # Results functions
    def is_scraped(self):
        self.log(f'Cmd: is_scraped')
        for item in self.seasons:
            for index, season in item.items():
                if season.is_scraped() is False:
                    self.log(f'{season.key} scrape status: Incomplete')
                    self.scraped_flag = False
                    if index not in self.to_scrape:
                        self.log(f'Index {index} added to scrape list')
                        if index not in self.to_scrape:
                            self.to_scrape.append(index)
        self.log(f'Competition scrape status: {"In" * (not self.scraped_flag)}Complete\t'
                 f'Key: {self.key}')
        return self.scraped_flag

    def to_json(self, name: str = None, file: bool = False):
        self.log(f'Cmd: to_json\t'
                 f'Key: {self.key}\t'
                 f'Url: {self.url}')
        data = {"Info": {'URL': self.url,
                         'Name': self.key,
                         'Tables': self.get_tables()
                         },
                'Seasons': self.get_seasons_as_json()
                }
        if file:
            name = name if name is not None else f'{self.key}'
            self.log('Cmd: File saving...')
            save(data=data, name=f'{name}.json')
        else:
            self.log('Cmd: Retrieve data')
            return data

    def log(self, message: str, level: int = 10):
        if self.logger is not None:
            if level is not None:
                self.logger.log(level, message)
