#!/usr/bin/env python3

from Scripts.Utility.db import DB
from Scripts.Utility.logger import Logger
from Scripts.Utility.requests import connect


class Scraper:
    logger = None

    def __init__(self, link: str, name: str = None):
        self.add_logger(name=name) if name is str else self.add_logger()
        self.db_client = DB(self.logger)
        self.r_json = connect(url=link, return_text=False, return_json=True)

    def add_logger(self, name: str = "NoName.log"):
        self.logger = Logger(f'{name}.log').get_logger()
