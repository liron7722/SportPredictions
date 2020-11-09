#!/usr/bin/env python3

import pandas as pd
from bs4 import BeautifulSoup
from Scripts.Utility.json import save
from Scripts.Utility.requests import connect
from Scripts.Scraper.Sports.Soccer.MatchReport import MatchReport


class Season:
    base: str = 'https://fbref.com/'  # main url
    scraped_flag: bool = False
    fixtures: list = []
    nationalities: pd.DataFrame = None
    to_scrape = []

    def __init__(self, key, url, info):
        self.key = key
        self.base_info = info
        self.url = self.base + url
        text = connect(url=self.url, return_text=True)
        page_text = text.replace('<!--\n', '')  # replace method used to get tables in comments
        self.soup = BeautifulSoup(page_text, "lxml")

    def db_load(self):
        pass  # TODO

    def get_base_info(self):
        return self.base_info.to_json()

    def get_fixtures(self):
        values = []
        # gather all the fixtures of the season
        for item in self.fixtures:
            for fixture in item.values():
                values.append(fixture)
        # send the fixtures json back
        return [fixture.to_json() for fixture in values]

    def get_nationalities(self):
        if self.nationalities is not None:  # in case this season don't got nationalities page
            return [self.nationalities.iloc[i].to_json() for i in range(len(self.nationalities))]
        return []

    def add_fixture(self, url: str, index: int):
        temp = MatchReport(url)  # create fixture + scrape
        temp.parse()  # fixture parse
        self.fixtures.append({index: temp})  # add fixture to the list

    def scrape_fixtures(self, url, scrape_list: list = None):
        text = connect(url=self.base + url, return_text=True)
        soup = BeautifulSoup(text, "lxml")
        html_urls = soup.find('tbody').find_all('tr')  # get links of all fixtures
        scrape_list = [j for j in range(len(html_urls))] if scrape_list is None else scrape_list
        for i in scrape_list:
            temp = html_urls[i].contents[-2]
            try:
                url = temp.find('a').get('href').removeprefix('/')  # Fixture url
                self.add_fixture(self.base + url, i)
            except AttributeError:
                if len(temp.attrs) != 2:  # 2 is attrs of the table spacer
                    self.to_scrape.append(i)  # fixture don't have match link - most likely postpone or yet to happen

    def scrape_nationalities(self, url):
        text = connect(url=self.base + url, return_text=True)
        soup = BeautifulSoup(text, "lxml")
        df = pd.read_html(str(soup))[0]
        self.nationalities = df[df.List != 'List']  # remove row with used as header in the middle of the table

    def navbar(self):
        res = dict()
        # rest of the inner navbar
        temp = self.soup.find_all('ul', {'class': "hoversmooth"})[1]  # navbar html
        values = temp.find_all('li', {'class': "full"})
        for val in values:
            if 'Fixtures' in val.find('a').get('href'):
                res['Fixtures'] = val.find('a').get('href').removeprefix('/')
            elif 'Nationalities' in val.find('a').get('href'):
                res['Nationalities'] = val.find('a').get('href').removeprefix('/')
        return res

    def scrape(self):
        funcs = {'Fixtures': self.scrape_fixtures, 'Nationalities': self.scrape_nationalities}
        temp = self.navbar()  # get inner navbar links
        for key, url in temp.items():
            funcs[key](url)
        #else:
        #    self.scrape_fixtures(url=temp['Fixtures'], scrape_list=self.to_scrape)  # TODO if db loaded
        self.scraped_flag = True

    def is_scraped(self):
        for item in self.fixtures:
            for index, fixture in item.items():
                if fixture.is_scraped() is False:
                    self.scraped_flag = False
                    if index not in self.to_scrape:
                        self.to_scrape.append(index)
        return self.scraped_flag

    def to_json(self, name: str = None, to_file: bool = False):
        data = {'URL': self.url,
                'Name': self.key,
                'Basic Info': self.get_base_info(),
                'Advance Info': {
                    'Fixtures': self.get_fixtures(),
                    'Nationalities': self.get_nationalities()
                    },
                'To Scrape': self.to_scrape
                }
        if to_file:
            save(data=data, name=name)
        else:
            return data

    def run(self):
        self.scrape()
