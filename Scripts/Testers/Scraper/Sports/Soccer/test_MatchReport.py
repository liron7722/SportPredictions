#!/usr/bin/env python3

import os
import unittest
from Scripts.Utility.json import read
from Scripts.Scraper.Sports.Soccer.MatchReport import MatchReport

BASE_PATH = f"{os.path.dirname(os.path.realpath(''))}{os.sep}SportPredictions{os.sep}"


class TestMatchReport(unittest.TestCase):
    mrs = {}

    @classmethod
    def setUpClass(cls) -> None:
        result_file = 'Scripts/Testers/Scraper/Sports/Soccer/testFiles/matchReport.json'
        cls.expected_results = read(BASE_PATH + result_file)
        cls.links = {
                # league game - no fans
                '0.json': 'en/matches/bf52349b/Fulham-Arsenal-September-12-2020-Premier-League',
                # cup game - no extra time
                '1.json': 'en/matches/914e23ed/Brentford-Fulham-August-4-2020-Championship',
                # cup game with penalties
                '2.json': 'en/matches/1f445267/Arsenal-Liverpool-August-29-2020-FA-Community-Shield',
                # league game - weird stats
                '3.json': 'en/matches/98b4b5b6/Aston-Villa-Sheffield-United-September-21-2020-Premier-League',
                # cup game - with fans
                '4.json': 'en/matches/c9d7e48c/Russia-Saudi-Arabia-June-14-2018-FIFA-World-Cup',
                # old event - missing starting players, stats, extra stats
                '5.json': 'en/matches/2bb1b361/Uruguay-Argentina-July-30-1930-FIFA-World-Cup',
            }
        for key, url in cls.links.items():
            cls.mrs[key] = MatchReport(url=url)
            cls.mrs[key].parse()

    @classmethod
    def tearDownClass(cls) -> None:
        # Removing files created by test_to_json with file=True
        for key in cls.mrs.keys():
            if os.path.exists(key):
                os.remove(key)

    def test_get_score_box(self):
        func_key = 'Score Box'
        for key, match in self.mrs.items():
            self.assertEqual(self.mrs[key].get_score_box(), self.expected_results[key][func_key])

    def test_get_register_teams(self):
        func_key = 'Register Teams'
        for key, match in self.mrs.items():
            self.assertEqual(self.mrs[key].get_register_teams(), self.expected_results[key][func_key])

    def test_get_events(self):
        func_key = 'Events'
        for key, match in self.mrs.items():
            self.assertEqual(self.mrs[key].get_events(), self.expected_results[key][func_key])

    def test_get_stats(self):
        func_key = 'Stats'
        for key, match in self.mrs.items():
            self.assertEqual(self.mrs[key].get_stats(), self.expected_results[key][func_key])

    def test_get_extra_stats(self):
        func_key = 'Extra Stats'
        for key, match in self.mrs.items():
            self.assertEqual(self.mrs[key].get_extra_stats(), self.expected_results[key][func_key])

    def test_get_dict_tables(self):
        func_key = 'Dict Tables'
        for key, match in self.mrs.items():
            self.assertEqual(self.mrs[key].get_dict_tables(), self.expected_results[key][func_key])

    def test_is_scraped(self):
        for match in self.mrs.values():
            self.assertTrue(match.is_scraped())

    def test_json_to_file(self):
        for key, match in self.mrs.items():
            match.to_file(name=key)

    @staticmethod
    def start():
        unittest.main()


if __name__ == '__main__':
    unittest.main()
