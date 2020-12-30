import os
import unittest
import pandas as pd
from Scripts.Utility.db import DB
from Scripts.Utility.json import read
from Scripts.Utility.logger import Logger
from Scripts.Scraper.Soccer.Season import Season

BASE_PATH = f"{os.path.dirname(os.path.realpath(''))}{os.sep}SportPredictions{os.sep}"


class TestSeason(unittest.TestCase):
    db = None
    seasons = {}

    @classmethod
    def setUpClass(cls) -> None:
        cls.db = DB('SOCCER')
        logger = Logger(f'Season Test.log').get_logger()
        result_file = 'Scripts/Testers/Scraper/Sports/Soccer/testFiles/season.json'
        cls.expected_results = read(BASE_PATH + result_file)
        cls.links = {
            '10.json': 'en/comps/9/Premier-League-Stats',
            '11.json': 'en/comps/1/FIFA-World-Cup-Stats',
        }
        info = pd.DataFrame([[1, 2]], columns=list('AB'))  # Dummy data
        for key, url in cls.links.items():
            cls.seasons[key] = Season(key=key, url=url, info=info, logger=logger)
            cls.seasons[key].scrape()

    @classmethod
    def tearDownClass(cls) -> None:
        # Removing files created by test_to_json with file=True
        for key in cls.seasons.keys():
            if os.path.exists(key):
                os.remove(key)  # remove testing files
            if key in cls.db.get_db_names():
                cls.db.client.drop_database(key.replace('.', '_'))  # remove testing databases

    def test_nationalities(self):
        raise NotImplementedError  # TODO

    def test_navbar(self):
        raise NotImplementedError  # TODO

    def test_results(self):
        for key, season in self.seasons.items():
            self.assertEqual(season.to_json(), self.expected_results[key])

    def test_json_to_file(self):
        for key, season in self.seasons.items():
            season.to_file(name=key)

    def test_db_save(self):
        for key, season in self.seasons.items():
            season.add_db(db=self.db)
            season.save()

    @staticmethod
    def start():
        print("This may take few minutes for each season testing, Be patient!")
        unittest.main()


if __name__ == '__main__':
    unittest.main()
