#!/usr/bin/env python3

# Utility
import pandas as pd
from bs4 import BeautifulSoup
from Scripts.Utility.path import get_files, sep
from Scripts.Utility.time import time_wrapper
from Scripts.Utility.requests import connect
from Scripts.Utility.exceptions import PageNotLoaded
from Scripts.Utility.resources import is_there_free_memory
from Scripts.Utility.json import read, BASE_PATH as PRODUCT_PATH
# Scrape
from Scripts.Scraper.Soccer.basic import Basic
from Scripts.Scraper.Soccer.Season import Season


class Competition(Basic):
    def __init__(self, key, url, logger=None, db=None):
        # Initialize
        super().__init__(url=url, key=key, logger=logger, db=db)
        self.tables = None
        self.seasons = list()
        self.seasons_urls = list()
        self.to_scrape = list()
        self.log(f'Competition Initialize with Key: {key},\tUrl: {url}')
        # connect and parse
        r_text = connect(url=self.url)
        page_text = r_text.replace('<!--\n', '')
        self.soup = BeautifulSoup(page_text, "lxml")

    # Getters
    def get_seasons_as_json(self):
        return [season.to_json() for season in self.seasons]

    def get_tables(self):
        if type(self.tables) is list:
            return self.tables
        else:
            return [[table.iloc[i].to_json() for i in range(len(table))] for table in self.tables]

    # Load
    def load_seasons(self, season):
        self.log(f'Cmd: load_seasons')
        url = season['URL'].replace(self.base, '')
        if len(season['To Scrape']) > 0:
            basic = season
            basic.pop('URL')
            scrape_list = basic.pop('To Scrape')
            basic.pop('Nationalities')
            self.add_season(url=url, info=basic, to_scrape=scrape_list)
        else:
            self.seasons_urls.append(url)

    # Local load
    def load_files(self, name):
        self.log(f'Cmd: load_files')
        path = f'{PRODUCT_PATH}{name}{sep}'
        for file in get_files(folder_path=path):
            temp = read(file)
            basic = temp['Basic Info']
            basic['URL'] = temp['URL']
            basic['To Scrape'] = temp['To Scrape']
            self.load_seasons(season=basic)

    # DB Load
    def load_db(self, name):
        self.log(f'Cmd: load_db')
        db = self.db_client.get_db(name=name)  # get db
        for coll_name in self.db_client.get_collections_names(db=db):
            if coll_name == 'Info':
                continue
            collection = self.db_client.get_collection(name=coll_name, db=db)  # get collection
            basic = collection.find({"Season": coll_name}).next()  # get season basic info
            basic.pop('_id')  # pop document id
            self.load_seasons(season=basic)

    def load(self):
        self.log(f'Cmd: load')
        name = self.get_name().replace('-Stats', '')
        if self.db_client is not None:  # load data from db
            self.load_db(name=name)
        else:  # load data from local files
            self.load_files(name=name)

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

    def seasons_to_db(self):
        self.log('Cmd: save')
        for season in self.seasons:
            if season.saved_flag is False:
                season.save()

    def save(self):
        self.seasons_to_db()

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

            temp = Season(key=self.key, url=url, info=info, logger=self.logger, db=self.db_client, path=self.path,
                          to_scrape=to_scrape)
            temp.run()

            # if is_there_free_memory():  # save to memory
            #    self.seasons.append(temp)

        else:  # season was loaded from db
            self.log(f'Already added')

    def get_history_link(self):
        self.log(f'Cmd: get_history_link')
        temp = self.soup.find_all('ul', {'class': "hoversmooth"})[1]  # navbar html
        # navbar index (history) url
        url = temp.find('li', {'class': "index"}).find('a').get('href')
        return self.base + self.extract_url(url)

    def scrape_seasons(self, soup: BeautifulSoup, scrape_list: list):
        self.log(f'Cmd: scrape_seasons')
        df = pd.read_html(str(soup))[0]  # get history full table
        urls = soup.find('tbody').find_all('tr')  # get links of all seasons
        scrape_list = [j for j in range(len(urls))] if len(scrape_list) == 0 else scrape_list
        self.to_scrape = []  # reset scrape list
        self.log(f'Info: Going to scrape {len(scrape_list)} Seasons')
        for i in scrape_list:
            info = df.iloc[i]  # general information

            if urls[i].contents[0].find('a') is None:  # this row don't have a url
                self.log(f'Skipped row {i} while trying to parse season table')
                continue
            else:
                url = urls[i].contents[0].find('a').get('href')  # Competition url
                url = self.extract_url(url)
            try:
                time_wrapper(func=self.add_season, logger=self.logger)(url=url, info=info)
                self.log(f'Season {i + 1} of {len(scrape_list)} successfully scrape at Url: {url}', level=20)
            except PageNotLoaded and AttributeError and IndexError and Exception:
                message = f'Error accord,\tSeason {i}/{len(scrape_list)} failed scrape at Url: {url}'
                self.logger.exception(message) if self.logger is not None else print(message)
                if i not in self.to_scrape:  # avoiding duplicate
                    self.to_scrape.append(i)

    def scrape(self):
        self.log(f'Cmd: scrape\t'
                 f'Key: {self.key}\t'
                 f'Url: {self.url}')
        link = self.get_history_link()
        soup = BeautifulSoup(connect(link), "lxml")
        # Starting call scrape for each season
        time_wrapper(func=self.scrape_seasons, logger=self.logger)(soup, self.to_scrape)

    def run(self):
        self.load()  # load data to know what left to scrape
        self.scrape()  # scrape data
        self.save()  # save data
