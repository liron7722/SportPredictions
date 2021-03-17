#!/usr/bin/env python3

# Utility Imports
from os import environ
from re import findall
from gc import enable as garbage_collector_enable
from Scripts.Utility.db import DB
from Scripts.Utility.logger import Logger
from Scripts.Utility.requests import connect
from Scripts.Utility.time import call_sleep, time_wrapper
from Scripts.Utility.exceptions import PageNotLoaded, ParseError
# Scraper Imports
from Scripts.Scraper.Soccer.Competition import Competition

ENV = environ.get('ENV') or 'Production'


class SoccerScraper:
    key = 'SOCCER'
    url = 'https://fbref.com/short/inc/main_nav_menu.json'  # Competitions link
    competitions = []
    logger: Logger = None
    db_client: DB = None

    def __init__(self, url: str = None):
        garbage_collector_enable()
        self.url = self.url if url is None else url
        self.logger = Logger(f'soccer_scraper', api=False)
        self.db_client = DB(key=f'{self.key}_SPORT_PREDICTION', logger=self.logger)
        self.r_json = connect(url=url, return_text=False, return_json=True)

    # Scrape
    def add_competition(self, key, url: str):
        flag = not (key in [comp.key for comp in self.competitions])  # Check competition not already added before
        if flag and key not in ['2020-2021', '2022']:  # Current and future season, will be scraped in other urls
            self.logger.log(f'Cmd: add_competitions,\tKey: {key},\tUrl: {url}', level=10)
            comp = Competition(key=key, url=url, logger=self.logger, db=self.db_client)
            try:
                time_wrapper(func=comp.run, logger=self.logger)()  # Competition scrape
            except PageNotLoaded or ParseError:
                message = f'Error stopped in SoccerScraper script, scrape_competitions method\t' \
                          f'Competition Key: {comp.key}'
                self.logger.log(message=message, level=40)

    def scrape(self):
        self.logger.log('Cmd: scrape', level=20)
        for item in self.r_json:
            if item['target'] == 'header_comps':
                temp = findall('/(.*)\"', item['html'].replace(';', '\n'))
                for val in temp:
                    self.add_competition(key=val.split('/')[-1], url=val)

    # Main
    def run(self, loop: bool = True):
        self.logger.log(f'Cmd: run\tKey: {self.key}\tUrl: {self.url}', level=20)
        while loop:
            time_wrapper(func=self.scrape, logger=self.logger)()
            call_sleep(minutes=10, logger=self.logger)


if __name__ == '__main__':
    soccer_scraper = SoccerScraper()
    soccer_scraper.run(loop=False)
