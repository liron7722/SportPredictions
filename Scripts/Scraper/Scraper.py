#!/usr/bin/env python3

from os import environ
from Scripts.Utility.db import DB
from Scripts.Utility.logger import Logger
from Scripts.Utility.requests import connect


class Scraper:
    ENV = 'Development'
    logger = None
    db_client = None

    def __init__(self, url: str, name: str = None, to_db: bool = True):
        self.add_logger(name=name) if name is not None else self.add_logger()
        self.db_client = DB(key=name, logger=self.logger) if to_db else None
        self.r_json = connect(url=url, return_text=False, return_json=True)
        self.ENV = environ.get(f'{name}_SCRAPER_ENV')

    def add_logger(self, name: str = "NoName"):
        self.logger = Logger(f'{name}.log').get_logger()

    # Logger
    def log(self, message: str, level: int = 10):
        if self.logger is not None:
            if self.ENV == 'Development':
                level = 10
            elif self.ENV == 'Production':
                level = 20
            self.logger.log(level, message)
