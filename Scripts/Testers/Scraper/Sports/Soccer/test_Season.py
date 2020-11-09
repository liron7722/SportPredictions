import os
import unittest
import pandas as pd
from Scripts.Utility.json import read
from Scripts.Scraper.Sports.Soccer.Season import Season

BASE_PATH = 'C:/Users/Liron/Documents/githubProjects/SportPredictions/'


class TestSeason(unittest.TestCase):
    seasons = {}

    @classmethod
    def setUpClass(cls) -> None:
        result_file = 'Scripts/Testers/Scraper/Sports/Soccer/testFiles/matchReport.json'
        cls.expected_results = read(BASE_PATH + result_file)
        cls.links = {
            '10.json': 'en/comps/9/Premier-League-Stats',
            '11.json': 'en/comps/1/FIFA-World-Cup-Stats',
        }
        for key, url in cls.links.items():
            cls.seasons[key] = Season(key=key, url=url, info=pd.DataFrame([[1, 2]], columns=list('AB')))
            cls.seasons[key].run()

    @classmethod
    def tearDownClass(cls) -> None:
        # Removing files created by test_to_json with file=True
        for key in cls.seasons.keys():
            if os.path.exists(key):
                os.remove(key)

    def test_nationalities(self):
        pass  # TODO

    def test_navbar(self):
        pass  # TODO

    def test_is_scraped(self):
        for season in self.seasons.values():
            n = len(season.to_scrape)
            if season.is_scraped():
                self.assertEqual(0, n)
            else:
                self.assertNotEqual(0, n)

    def test_to_json(self):
        for key, season in self.seasons.items():
            season.to_json(name=key, to_file=True)

    @staticmethod
    def start():
        unittest.main()


if __name__ == '__main__':
    unittest.main()
