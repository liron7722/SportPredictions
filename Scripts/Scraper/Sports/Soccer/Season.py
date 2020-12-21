#!/usr/bin/env python3

import re
import pandas as pd
from bs4 import BeautifulSoup
from Scripts.Utility.requests import connect
from Scripts.Scraper.Sports.Soccer.basic import Basic
from Scripts.Scraper.Sports.Soccer.MatchReport import MatchReport


class Season(Basic):
    def __init__(self, key, url, info, logger=None, db=None, path: str = None):
        # initialize
        super().__init__(url=url, key=key, logger=logger, db=db, path=path)
        self.base_info = info
        self.fixtures = list()
        self.to_scrape = list()
        self.nationalities = None
        # connect and parse
        text = connect(url=self.url, return_text=True)
        page_text = text.replace('<!--\n', '')  # replace used to get tables in comments but do appear on the site
        self.soup = BeautifulSoup(page_text, "lxml")

    # Utility functions
    def get_name(self):
        if self.db_client is None:  # data will be saved on file with year in the name
            year = "-".join(re.findall('\d{4}', self.url.split('/')[-1]))
            return f'{self.key}_{year}' if len(year) > 0 else super().get_name()
        else:  # data will be save under one db
            return super().get_name()

    # Preparation functions
    def get_base_info(self):
        if type(self.base_info) in [pd.core.series.Series, pd.core.frame.DataFrame]:  # Ignore warnings
            return self.base_info.to_json()
        else:  # already as json because loaded from db
            return self.base_info

    def get_fixtures(self):
        # send the fixtures json back
        return [fixture.to_json() for fixture in self.fixtures]

    def get_nationalities(self):
        if self.nationalities is not None:  # in case this season don't got nationalities page
            return [self.nationalities.iloc[i].to_json() for i in range(len(self.nationalities))]
        return []

    # DB Save
    @staticmethod
    def set_data_to_update(new, old):
        header = 'Advance Info'
        extend_list = ['Fixtures']
        replace_list = ['Nationalities']
        for key in extend_list + replace_list:
            if key in extend_list:
                new[header][key].extend(old[header][key])
            elif key in replace_list:
                if len(new[header][key]) == 0:
                    new[header][key] = old[header][key]
        return new

    def to_db(self, db, name="Seasons"):
        data = self.to_json()
        fil = {"URL": self.url}
        collection = self.db_client.get_collection(name=name, db=db)
        # update
        if self.db_client.is_document_exist(collection=collection, fil=fil):
            original_data = collection.find(fil).next()  # get original data from db
            data = self.set_data_to_update(data, original_data)
            self.update_db(name, collection=collection, fil=fil, data=data)
        # insert
        else:
            self.insert_to_db(name, collection=collection, data=data)

    def to_json(self, name: str = None):
        super().to_json()
        return {'URL': self.url,
                'Name': self.key,
                'Basic Info': self.get_base_info(),
                'Advance Info': {
                    'Fixtures': self.get_fixtures(),
                    'Nationalities': self.get_nationalities()
                    },
                'To Scrape': self.to_scrape
                }

    # Scrape and Parse functions
    def parse_general_info(self):
        self.log(f'Cmd: parse_general_info')
        dfs = pd.read_html(str(self.soup))
        if len(dfs) > 0:
            self.tables = []
        for table in dfs:
            table = self.change_col_name(table)
            table = self.change_nan(table)
            self.tables.append(table)

    def navbar(self):
        res = dict()
        # rest of the inner navbar
        temp = self.soup.find_all('ul', {'class': "hoversmooth"})[1]  # navbar html
        values = temp.find_all('li', {'class': "full"})
        for val in values:
            url = val.find('a').get('href')
            if 'Fixtures' in url:
                res['Fixtures'] = self.extract_url(url)
            elif 'Nationalities' in url:
                res['Nationalities'] = self.extract_url(url)
        return res

    def add_fixture(self, url: str):
        temp = MatchReport(url)  # create fixture + scrape
        temp.parse()  # fixture parse
        self.fixtures.append(temp)  # add fixture to the list

    def scrape_nationalities(self, url: str):
        text = connect(url=url, return_text=True)
        soup = BeautifulSoup(text, "lxml")
        df = pd.read_html(str(soup))[0]
        self.nationalities = df[df.List != 'List']  # remove row with used as header in the middle of the table

    def scrape_fixtures(self, url: str):
        text = connect(url=url, return_text=True)
        soup = BeautifulSoup(text, "lxml")
        html_urls = soup.find('tbody').find_all('tr')  # get links of all fixtures
        scrape_list = [j for j in range(len(html_urls))] if len(self.to_scrape) == 0 else self.to_scrape
        self.log(f'Going to scrape {len(scrape_list)} fixtures')
        for i in scrape_list:
            try:
                temp = html_urls[i].contents[-2]
            except IndexError:
                message = f'Got error while getting match (row {i}) in match list\tAt url: {url}'
                self.logger.exception(message) if self.logger is not None else print(message)
                continue
            try:
                if html_urls[i].contents[-1] == 'Match Cancelled' or temp.text == 'Head-to-Head' or len(temp.attrs) != 2:
                    self.to_scrape.append(i)  # fixture don't have match link - yet to happen or postpone or cancelled
                elif temp.text == 'Match Report':
                    url = self.extract_url(temp.find('a').get('href'))  # Fixture url
                    self.add_fixture(url)
            except AttributeError:
                if len(temp.attrs) != 2:  # 2 is attrs of the table spacer
                    self.to_scrape.append(i)  # fixture don't have match link - most likely postpone

    def scrape(self):
        self.parse_general_info()
        funcs = {'Fixtures': self.scrape_fixtures, 'Nationalities': self.scrape_nationalities}
        temp = self.navbar()  # get inner navbar links
        for key, url in temp.items():
            funcs[key](url=self.base + url)  # Ignore or make it based of the key calls

    def run(self):
        self.scrape()  # scrape data
        self.save()  # save data
