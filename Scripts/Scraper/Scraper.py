#!/usr/bin/env python3

from Scripts.Utility.db import DB
from Scripts.Utility.logger import Logger
from Scripts.Utility.requests import connect


class Scraper:
    def __init__(self, link: str, name: str = "NoName.log"):
        self.logger = Logger(name).get_logger()
        self.db_client = DB(self.logger)
        self.r_json = connect(url=link, return_text=False, return_json=True)
