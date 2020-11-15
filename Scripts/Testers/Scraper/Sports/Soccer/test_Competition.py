import os
import unittest
from Scripts.Utility.json import read
from Scripts.Scraper.Sports.Soccer.Competition import Competition

BASE_PATH = f"{os.path.dirname(os.path.realpath(''))}{os.sep}SportPredictions{os.sep}"


class TestCompetition(unittest.TestCase):
    competitions = {}

    @classmethod
    def setUpClass(cls) -> None:
        result_file = 'Scripts/Testers/Scraper/Sports/Soccer/testFiles/competition.json'
        cls.expected_results = read(BASE_PATH + result_file)
        cls.links = {
            '100.json': 'en/comps/9/history/Premier-League-Seasons',  # Casual link of league
            # '101.json': 'en/comps/1/history/World-Cup-Seasons',  # History link of a tournament
        }
        for key, url in cls.links.items():
            cls.competitions[key] = Competition(key=key, url=url)
            cls.competitions[key].run()

    @classmethod
    def tearDownClass(cls) -> None:
        # Removing files created by test_to_json with to_file=True
        for key in cls.competitions.keys():
            if os.path.exists(key):
                os.remove(key)

    def test_is_scraped(self):
        for competition in self.competitions.values():
            n = len(competition.to_scrape)
            if competition.is_scraped():
                self.assertEqual(0, n)
            else:
                self.assertNotEqual(0, n)

    def test_to_json(self):
        for key, competition in self.competitions.items():
            competition.to_json(name=key, to_file=True)

    @staticmethod
    def start():
        print("This may take around a hour for each competition testing, Be patient!")
        unittest.main()


if __name__ == '__main__':
    unittest.main()