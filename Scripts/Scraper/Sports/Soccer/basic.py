import pandas as pd
from os import environ
from Scripts.Utility.json import save


class Basic:
    ENV = 'Development'
    base: str = 'https://fbref.com/'  # main url
    key: str = None
    url: str = None
    path: str = None
    tables = None
    logger = None
    db_client = None
    scraped_flag: bool = False
    saved_flag: bool = False

    def __init__(self, key, url, logger=None, db=None, path: str = None):
        self.key = key
        self.url = self.base + url
        self.add_db(db=db)
        self.add_logger(logger=logger)
        self.add_path(path=path)
        self.ENV = environ.get(f'SOCCER_SCRAPER_ENV')

    # Setters
    def add_logger(self, logger):
        self.logger = logger

    def add_db(self, db):
        self.db_client = db

    def add_path(self, path: str = None):
        self.path = self.get_name() if path is None else path

    # Utility functions
    def log(self, message: str, level: int = None):
        if self.logger is not None:
            if level is None:
                if self.ENV == 'Development':
                    level = 10
                elif self.ENV == 'Production':
                    level = 20
            self.logger.log(level, message)

    # Local Save
    def to_file(self, name: str):
        self.log('Cmd: File saving...')
        name = name if '.json' in name else f'{name}.json'
        save(data=self.to_json(), name=name, path=self.path)

    def is_scraped(self):
        return self.scraped_flag

    # DB
    def insert_to_db(self, name, collection, data):
        self.log(f'Cmd: Insert new {name} document,\tUrl: {self.url}')
        self.db_client.insert_document(collection=collection, data=data)

    def update_db(self, name, collection, fil, data):
        self.log(f'Cmd: Update {name} document,\tUrl: {self.url}')
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
        self.log('Cmd: Retrieve data')

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
