#!/usr/bin/env python3

# Utility
import pandas as pd
from bs4 import BeautifulSoup
from Scripts.Utility.time import time_wrapper
from Scripts.Utility.requests import connect
from Scripts.Utility.exceptions import PageNotLoaded
from Scripts.Utility.resources import is_there_free_memory
# Scrape
from Scripts.Scraper.Sports.Soccer.basic import Basic
from Scripts.Scraper.Sports.Soccer.Season import Season


class Competition(Basic):
    tables = None
    seasons: list = []
    seasons_urls: list = []
    to_scrape: list = []

    def __init__(self, key, url, logger=None, db=None):
        super().__init__(url=url, key=key, logger=logger, db=db)
        self.log(f'Competition Initialize with Key: {key},\tUrl: {url}')
        r_text = connect(url=self.url)
        page_text = r_text.replace('<!--\n', '')
        self.soup = BeautifulSoup(page_text, "lxml")

    # Getters
    def get_seasons_as_json(self):
        return [season.to_json() for season in self.seasons]

    def get_tables(self):
        if self.tables is list:
            return self.tables
        else:
            return [[table.iloc[i].to_json() for i in range(len(table))] for table in self.tables]

    # DB Load
    def load_seasons(self, db, name='Seasons'):
        collection = self.db_client.get_collection(name=name, db=db)
        for season in collection.find({}):
            url = season['URL'].replace(self.base, '')
            if len(season['To Scrape']) > 0:
                self.add_season(url, season['Basic Info'])
            else:
                self.seasons_urls.append(url)

    def load_db(self):
        self.log(f'Cmd: load_db')
        if self.db_client is not None:  # db load
            name = self.get_name()
            db = self.db_client.get_db(name=name)
            self.load_seasons(db=db)
        else:
            self.log(f'Nothing to load')

    # DB Save
    def to_db(self, db, name="Info"):
        data = self.to_json()
        data.pop('Seasons')
        fil = {"URL": self.url}
        collection = self.db_client.get_collection(name=name, db=db)
        # update
        if self.db_client.is_document_exist(collection=collection, fil=fil):
            self.update_db(name, collection=collection, fil=fil, data=data)
        # insert
        else:
            self.insert_to_db(name, collection=collection, data=data)

    def season_to_db(self):
        self.log('Cmd: save')
        for season in self.seasons:
            if season.saved_flag is False:
                season.save()

    def save(self):
        self.season_to_db()
        super().save()

    # Json
    def to_json(self):
        super().to_json()
        return {"Info": {'URL': self.url,
                         'Name': self.key,
                         'Tables': self.get_tables()
                         },
                'Seasons': self.get_seasons_as_json()
                }

    # Scrape functions
    @time_wrapper
    def add_season(self, url: str, info, to_scrape: list = None):
        self.log(f'Cmd: add_season\t Url: {url}')
        if url not in self.seasons_urls:  # add new season or un finished scraped season
            self.log(f'Added season')
            self.seasons_urls.append(url)
            temp = Season(key=self.key, url=url, info=info, logger=self.logger, db=self.db_client, path=self.path)
            temp.to_scrape = [] if to_scrape is None else to_scrape
            temp.run()
            if is_there_free_memory():  # save to memory
                self.seasons.append(temp)
        else:  # season was loaded from db
            self.log(f'Already added')

    def get_history_link(self):
        self.log(f'Cmd: get_history_link')
        temp = self.soup.find_all('ul', {'class': "hoversmooth"})[1]  # navbar html
        # navbar index (history) url
        index_url = temp.find('li', {'class': "index"}).find('a').get('href').removeprefix('/')
        return self.base + index_url

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
                time_wrapper(func=self.add_season, logger=self.logger)(url=url, info=info)
                self.log(f'Season {i + 1} of {len(scrape_list)} successfully scrape at Url: {url}', level=20)
            except PageNotLoaded:
                message = f'Error accord,\tSeason {i}/{len(scrape_list)} failed scrape at Url: {url}'
                self.logger.exception(message) if self.logger is not None else print(message)
                if i not in self.to_scrape:  # avoiding duplicate
                    self.to_scrape.append(i)
        self.scraped_flag = True  # TODO: relevant?

    def scrape(self):
        self.log(f'Cmd: scrape\t'
                 f'Key: {self.key}\t'
                 f'Url: {self.url}')
        link = self.get_history_link()
        soup = BeautifulSoup(connect(link), "lxml")
        # Starting call scrape for each season
        time_wrapper(func=self.scrape_seasons, logger=self.logger)(soup, self.to_scrape)
        # self.is_scraped()  # Going throw all season check who didn't scrape   # TODO Decide what to do with this

    # Results functions
    def is_scraped(self):
        self.log(f'Cmd: is_scraped')
        for season in self.seasons:
            if season.is_scraped() is False:
                self.log(f'{season.key} scrape status: Incomplete')
                self.scraped_flag = False
        self.log(f'Competition scrape status: {"In" * (not self.scraped_flag)}Complete\t'
                 f'Key: {self.key}')
        return self.scraped_flag

    def run(self):
        self.load_db()  # load data to know what left to scrape
        self.scrape()  # scrape data
        self.save()  # save data
