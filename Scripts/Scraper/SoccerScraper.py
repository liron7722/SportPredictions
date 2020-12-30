#!/usr/bin/env python3

# Utility Imports
import re
from Scripts.Utility.time import call_sleep, time_wrapper
from Scripts.Utility.exceptions import PageNotLoaded, ParseError
# Scraper Imports
from Scripts.Scraper.Scraper import Scraper
from Scripts.Scraper.Soccer import Competition


class SoccerScraper(Scraper):
    key = 'SOCCER'
    url = 'https://fbref.com/short/inc/main_nav_menu.json'  # Competitions link
    competitions = []
    db_client = None

    def __init__(self, url: str = None):
        self.url = self.url if url is None else url
        super().__init__(url=self.url, name=self.key)

    # Scrape
    def add_competition(self, key, url: str):
        flag = not (key in [comp.key for comp in self.competitions])  # Check competition not already added before
        if flag and key not in ['2020-2021', '2022']:  # Current and future season, will be scraped in other urls
            self.log(f'Cmd: add_competitions,\tKey: {key},\tUrl: {url}')
            comp = Competition(key=key, url=url, logger=self.logger, db=self.db_client)
            try:
                time_wrapper(func=comp.run, logger=self.logger)()  # Competition scrape
            except PageNotLoaded or ParseError:
                message = f'Error stopped in SoccerScraper script, scrape_competitions method\t' \
                          f'Competition Key: {comp.key}'
                self.logger.exception(message) if self.logger is not None else print(message)
            # self.competitions.append(temp)

    def scrape(self):
        self.log('Cmd: scrape')
        for item in self.r_json:
            if item['target'] == 'header_comps':
                temp = re.findall('/(.*)\"', item['html'].replace(';', '\n'))
                for val in temp:
                    self.add_competition(key=val.split('/')[-1], url=val)

    # Main
    def run(self, loop: bool = True):
        self.log(f'Cmd: run\t'
                 f'Key: {self.key}\t'
                 f'Url: {self.url}')
        while loop:
            time_wrapper(func=self.scrape, logger=self.logger)()
            call_sleep(days=1, logger=self.logger)


if __name__ == '__main__':
    soccer_scraper = SoccerScraper()
    soccer_scraper.run(loop=False)
