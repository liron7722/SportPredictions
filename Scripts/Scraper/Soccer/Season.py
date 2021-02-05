#!/usr/bin/env python3

import re
import gc
import pandas as pd
from bs4 import BeautifulSoup
from Scripts.Utility.requests import connect
from Scripts.Utility.json import str_to_dict, encode_data
from Scripts.Utility.exceptions import PageNotLoaded, ParseError
from Scripts.Scraper.Soccer.basic import Basic
from Scripts.Scraper.Soccer.MatchReport import MatchReport


class Season(Basic):
    version = '1.0.0'

    def __init__(self, key, url, info, to_scrape: list = None, logger=None, db=None, path: str = None,
                 fixture_version=MatchReport.version, comp_name=None):
        # initialize
        super().__init__(url=url, key=key, logger=logger, db=db, path=path)
        self.comp_name = comp_name
        self.base_info = info
        self.fixtures = list()
        self.to_scrape = list() if to_scrape is None else to_scrape
        self.fixture_version = fixture_version
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
            return self.base_info.to_dict()
        elif type(self.base_info) is str:
            return str_to_dict(self.base_info)
        else:  # already as json because loaded from db
            return self.base_info

    def get_fixtures(self):
        # send the fixtures json back
        return [fixture.to_json() for fixture in self.fixtures]

    def get_nationalities(self):
        if self.nationalities is pd.core.frame.DataFrame:  # in case this season don't got nationalities page
            return [self.nationalities.iloc[i].to_json() for i in range(len(self.nationalities))]
        elif self.nationalities is not None:
            return self.nationalities
        else:
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

    def upload_to_db(self, collection, data):
        fil = {"URL": data['URL']}  # filter
        data = encode_data(data)  # Numpy encoder
        # update
        if self.db_client.is_document_exist(collection=collection, fil=fil):
            self.db_client.update_document(collection=collection, fil=fil, data=data)
        # insert
        else:
            self.db_client.insert_document(collection=collection, data=data)

    def to_db(self, db):
        data = self.to_json()
        # Data preparation
        basic = data['Basic Info']
        basic['URL'] = data['URL']
        basic['To Scrape'] = data['To Scrape']
        basic['Nationalities'] = data['Advance Info']['Nationalities']
        basic['Version'] = data['Version']
        basic['Fixture Version'] = data['Fixture Version']
        # Data upload
        collection = self.db_client.get_collection(name=basic['Season'], db=db)
        self.upload_to_db(collection=collection, data=basic)
        for match in data['Advance Info']['Fixtures']:
            self.upload_to_db(collection=collection, data=match)

    def upload_match(self, match):
        if self.comp_name is not None:
            season = self.get_base_info()['Season']
            name = self.comp_name.replace('-Stats', '')
            if self.db_client is not None:  # save data to db
                db = self.db_client.get_db(name=name)
                collection = self.db_client.get_collection(name=season, db=db)
                self.upload_to_db(collection=collection, data=match)
        else:
            print('dude fix it')

    def to_json(self, name: str = None):
        super().to_json()
        return {'URL': self.url,
                'Name': self.key,
                'Basic Info': self.get_base_info(),
                'Advance Info': {
                    'Fixtures': self.get_fixtures(),
                    'Nationalities': self.get_nationalities()
                    },
                'To Scrape': self.to_scrape,
                'Version': self.version,
                'Fixture Version': MatchReport.version
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
            if 'Nationalities' in url:
                res['Nationalities'] = self.extract_url(url)
            elif 'Fixtures' in url:
                res['Fixtures'] = self.extract_url(url)
        return res

    def add_fixture(self, url: str):
        temp = MatchReport(url)  # create fixture + scrape
        temp.parse()  # fixture parse
        # self.fixtures.append(temp)  # add fixture to the list
        self.upload_match(temp.to_json())

    def scrape_nationalities(self, url: str):
        text = connect(url=url, return_text=True)
        soup = BeautifulSoup(text, "lxml")
        df = pd.read_html(str(soup))[0]

        data = df[df.List != 'List']  # remove row with used as header in the middle of the table
        data = data.reset_index()
        data = data.to_dict()

        res = list()
        for i in range(len(data['Rk'].keys())):
            temp = {'Nation': None, '# Players': None, 'Min': None, 'List': None}
            res.append(temp)

            res[i]['Nation'] = data['Nation'][i]
            res[i]['# Players'] = data['# Players'][i]

            res[i]['Min'] = data['Min'][i]
            res[i]['Min'] = 0 if data['Min'][i] is None else data['Min'][i]

            if type(data['List'][i]) is float:  # In case no names in the table cell
                res[i]['List'] = list()
            else:
                lst = data['List'][i].split(', ')  # get all the names in the strings
                lst[-1] = lst[-1].replace(' ...', '')  # last name got 3 dots
                res[i]['List'] = lst

        self.nationalities = res

    def scrape_fixtures(self, url: str):
        text = connect(url=url, return_text=True)
        soup = BeautifulSoup(text, "lxml")
        html_urls = soup.find('tbody').find_all('tr')  # get links of all fixtures
        # if new version reset scrape list to scrape from start
        self.to_scrape = list() if MatchReport.version != self.fixture_version else self.to_scrape
        scrape_list = [j for j in range(len(html_urls))] if len(self.to_scrape) == 0 else self.to_scrape.copy()
        self.log(f'Going to scrape {len(scrape_list)} fixtures')
        self.to_scrape = list()
        for i in scrape_list:
            gc.collect()
            try:
                temp = html_urls[i].contents[-2]
            except IndexError:
                message = f'Got error while getting match (row {i}) in match list\tAt url: {url}'
                self.logger.exception(message) if self.logger is not None else print(message)
                continue
            try:
                if html_urls[i].contents[-1] == 'Match Cancelled' \
                        or temp.text == 'Match Postpone' \
                        or temp.text == 'Head-to-Head'\
                        or len(temp.attrs) != 2:
                    self.to_scrape.append(i)  # fixture don't have match link - yet to happen or postpone or cancelled
                elif temp.text == 'Match Report':
                    url = self.extract_url(temp.find('a').get('href'))  # Fixture url
                    self.add_fixture(url)
            except AttributeError:
                if len(temp.attrs) != 2:  # 2 is attrs of the table spacer
                    self.to_scrape.append(i)  # fixture don't have match link - most likely postpone
            except PageNotLoaded or ParseError:
                self.to_scrape.append(i)  # fixture page not loaded or parse issue
                self.logger.exception(f"Got issue with fixture at url: {url}")

    def scrape(self):
        self.parse_general_info()
        funcs = {'Nationalities': self.scrape_nationalities, 'Fixtures': self.scrape_fixtures}
        temp = self.navbar()  # get inner navbar links
        for key, url in temp.items():
            funcs[key](url=self.base + url)  # Ignore or make it based of the key calls

    def run(self):
        self.scrape()  # scrape data
        self.save()  # save data
