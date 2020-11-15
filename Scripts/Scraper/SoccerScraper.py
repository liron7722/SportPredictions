#!/usr/bin/env python3

import re
from Scripts.Utility.db import DB
from Scripts.Utility.json import save
from Scripts.Utility.time import call_sleep
from Scripts.Scraper.Scraper import Scraper
from Scripts.Scraper.Sports.Soccer.Competition import Competition
from Scripts.Utility.Exceptions import PageNotLoaded, ParseError


class SoccerScraper(Scraper):
    key = 'Soccer'
    url = 'https://fbref.com/short/inc/main_nav_menu.json'  # Competitions link
    competitions = []
    db_client = None
    logger = None

    def __init__(self, link: str = None):
        self.url = self.url if link is None else link
        super().__init__(self.url, f'{self.key}.log')
        self.db_client = DB(self.key)

    def get_collection_data(self, collection_list, db):
        data = dict()
        for c_name in collection_list:  # Info \ Seasons
            self.log(f'Got collection to load: {c_name}')
            collection = self.db_client.get_collection(name=c_name, db=db)
            # Season {Fixture \ Nationalities \ Info}, Info {URL \ Name \ Tables}
            data[c_name] = self.db_client.get_documents_list(collection=collection)  # documents
        return data

    def load_competition(self, data):
        values = data['Info'][0]
        temp = Competition(key=values['Name'], url=values['Url'], logger=self.logger)
        temp.load_db(data['Seasons'])
        self.competitions.append(temp)

    def load_db(self):
        self.log('Cmd: load_db')
        db_list = self.db_client.get_db_names()
        for db_name in db_list:
            if db_name in ['admin', 'config', 'local']:
                continue
            # Competition
            self.log(f'Got db to load: {db_name}')
            db = self.db_client.get_db(name=db_name)
            collection_list = self.db_client.get_collections_names(db=db)
            data = self.get_collection_data(collection_list, db=db)
            if 'Info' in collection_list:
                self.load_competition(data)

    def set_competitions(self, values: list):
        self.log('Cmd: set_competitions')
        for item in values:
            if item['target'] == 'header_comps':
                temp = re.findall('/(.*)\"', item['html'].replace(';', '\n'))
                for val in temp:
                    self.add_competition(
                        val.split('/')[-1],  # key
                        val  # url
                    )

    def add_competition(self, key, url: str):
        # Check competition not already added before
        flag = True
        for comp in self.competitions:
            if comp.key == key:
                flag = False
                break
        if flag and key not in ['2020-2021', '2022']:  # Current and future season, will be scraped in other urls
            self.log(f'Cmd: add_competitions,\tKey: {key},\tUrl: {url}')
            self.competitions.append(
                Competition(key=key, url=url, logger=self.logger)
            )

    def scrape_competitions(self):
        self.log('Cmd: scrape_competitions')
        self.log(f'Info: Going to scrape {len(self.competitions)} Competitions')
        for comp in self.competitions:
            try:
                comp.scrape()  # Competition scrape
            except PageNotLoaded or ParseError:
                message = f'Stopped in SoccerScraper script, scrape_competitions method' \
                          f'Competition Key: {comp.key}'
                self.logger.exception(message) if self.logger is not None else print(message)

    def scrape(self):
        self.log('Cmd: scrape')
        self.set_competitions(self.r_json)  # competitions from website
        self.scrape_competitions()  # start scrape

    def get_competitions(self):
        self.log('Cmd: get_competitions')
        return [comp.to_json() for comp in self.competitions]

    def to_json(self, name: str = None, to_file: bool = False):
        self.log(f'Cmd: to_json\t'
                 f'Key: {self.key}\t'
                 f'Url: {self.url}')
        data = self.get_competitions()
        if to_file:
            self.log('Cmd: File saving...')
            save(data=data, name=name)
        else:
            self.log('Cmd: Retrieve data')
            return data

    def season_to_db(self, season, collection):
        data = season.to_json()
        if self.db_client.is_exist(collection=collection, fil={"URL": season.url}):  # insert
            self.db_client.insert_document(collection=collection, data=data)
            self.log(f'Cmd: Insert new season document,\tUrl: {season.url}')
        else:  # update
            self.db_client.update_document(collection=collection,
                                           fil={'URL': season.url},
                                           data=data)
            self.log(f'Cmd: Update season document,\tUrl: {season.url}')

    def info_to_db(self, comp, collection):
        self.log('Cmd: info_to_db')
        if self.db_client.is_exist(collection=collection, fil={"URL": comp.url}):  # insert
            data = {'URL': comp.url,
                    'Tables': comp.get_tables()
                    }
            self.db_client.insert_document(collection=collection, data=data)
            self.log('Cmd: Insert new info document')
        else:  # update
            self.db_client.update_document(collection=collection,
                                           fil={"URL": comp.url},
                                           data={'Tables': comp.get_tables()})
            self.log('Cmd: Update info document')

    def get_competition_to_db(self, comp: Competition):
        self.log('Cmd: get_competition_to_db')
        db = self.db_client.get_db(name=comp.key)

        collection = self.db_client.get_collection(name='INFO', db=db)
        self.info_to_db(collection=collection, comp=comp)  # INFO

        collection = self.db_client.get_collection(name='Seasons', db=db)
        for season in comp.get_seasons_as_json():  # seasons
            self.season_to_db(season=season, collection=collection)

    def to_db(self):
        self.log('Cmd: to_db')
        for comp in self.competitions:
            self.get_competition_to_db(comp=comp)

    def run(self):
        self.log(f'Cmd: run\t'
                 f'Key: {self.key}\t'
                 f'Url: {self.url}')
        self.load_db()
        while True:
            self.scrape()
            self.to_db()
            call_sleep(days=1, logger=self.logger)

    def log(self, message: str, level: int = 10):
        if self.logger is not None:
            if level is not None:
                self.logger.log(level, message)


if __name__ == '__main__':
    soccer_scraper = SoccerScraper()
    soccer_scraper.load_db()
    soccer_scraper.scrape()
    soccer_scraper.to_db()
