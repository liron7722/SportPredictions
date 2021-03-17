import pandas as pd
from os import environ
from Scripts.Utility.json import save
from Scripts.Utility.db import DB
from Scripts.Utility.logger import Logger

ENV = environ.get(f'SOCCER_SCRAPER_ENV') or 'Production'


class Basic:
    base: str = 'https://fbref.com/'  # main url
    path: str = None
    logger: Logger = None
    db_client: DB = None

    def __init__(self, key: str, url: str, logger: Logger = None, db: DB = None, path: str = None):
        self.key = key
        self.url = self.base + url
        self.tables = None
        self.saved_flag = False
        self.db = db
        self.add_logger(logger=logger)
        self.add_path(path=path)

    # Setters
    def add_logger(self, logger: Logger = None):
        self.logger = Logger(f'soccer_scraper', api=False) if logger is None else logger

    def add_path(self, path: str = None):
        self.path = self.get_name() if path is None else path

    # Utility functions
    # Local Save
    def to_file(self, name: str):
        self.logger.log('Cmd: File saving...')
        name = name if '.json' in name else f'{name}.json'
        save(data=self.to_json(), name=name, path=self.path)

    # DB
    def insert_to_db(self, name, collection, data):
        self.logger.log(f'Cmd: Insert new {name} document,\tUrl: {self.url}')
        self.db_client.insert_document(collection=collection, data=data)

    def update_db(self, name, collection, fil, data):
        self.logger.log(f'Cmd: Update {name} document,\tUrl: {self.url}')
        self.db_client.update_document(collection=collection, fil=fil, data=data)

    def to_db(self, db):
        pass

    def save(self):
        name = self.get_name()
        if self.db_client is not None:  # save data to db
            db = self.db_client.get_db(name=name)
            self.to_db(db=db)
        else:  # save data to local file
            self.to_file(name=name)
        self.saved_flag = True

    # Misc
    def to_json(self):
        self.logger.log('Cmd: Retrieve data')

    def get_name(self):
        return self.key.replace('.', '_') if self.key is not None else ''

    @staticmethod
    def ascii_name_fix(name: str):
        return name.replace('\xa0', ' ')

    @staticmethod
    def change_nan(table):
        return table.where(pd.notnull(table), None)  # Nan to None

    @staticmethod
    def change_col_name(table):
        # Given better col name
        cols = table.columns
        if type(cols) == pd.core.indexes.multi.MultiIndex:
            table.columns = [f"{'General' if 'Unnamed' in col[0] else col[0]} - {col[1]}" for col in cols]
        return table

    @staticmethod
    def extract_url(url):
        return url[1:] if url[0] == '/' else url  # python3.8
