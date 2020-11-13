#!/usr/bin/env python3

import sys
# Scraper Imports
from Scripts.Scraper.SoccerScraper import SoccerScraper
# Analyzers Imports

# Models Imports

# Tests Imports
# Scraper Tests
# from Scripts.Testers.Scraper.Sports.Soccer.test_MatchReport import TestMatchReport
from Scripts.Testers.Scraper.Sports.Soccer.test_Season import TestSeason
# from Scripts.Testers.Scraper.Sports.Soccer.test_Competition import TestCompetition
# Analyzers Tests

# Models Tests


class Index:
    @staticmethod
    def run_soccer_scraper():
        soccer_scraper = SoccerScraper()
        soccer_scraper.run()

    def scrapers_menu(self, choice: int = None):
        functions = {1: self.run_soccer_scraper,
                     }
        if choice is None:
            choice = int(input("Enter which function you want to run:\n"
                               "1: run_soccer_scraper\n"
                               ))
        if len(functions) >= choice > 0:
            func = functions[choice]
            func()

    def tests_menu(self, choice: int = None):
        functions = {1: self.run_match_report_test,
                     2: self.run_season_test,
                     3: self.run_competition_test,
                     4: self.run_all_tests,
                     }
        if choice is None:
            choice = int(input("Enter which function you want to run:\n"
                               "1: run_match_report_test\n"
                               "2: run_season_test\n"
                               "3: run_competition_test\n"
                               "4: run_all_tests\n"
                               ))
        if len(functions) >= choice > 0:
            func = functions[choice]
            func()

    def run_all_tests(self):
        tests = [self.run_match_report_test,
                 self.run_season_test,
                 self.run_competition_test,
                 ]
        for test in tests:
            test()

    @staticmethod
    def run_match_report_test():
        pass  # TestMatchReport().start()

    @staticmethod
    def run_season_test():
        TestSeason().start()

    @staticmethod
    def run_competition_test():
        pass  # TestCompetition().start()


def init(index):
    functions = {1: index.scrapers_menu,
                 2: index.tests_menu,
                 }
    if len(sys.argv) > 1:
        choice = int(sys.argv[1])

    else:
        choice = int(input("Enter which function you want to run:\n"
                           "1: Scrapers Menu\n"
                           "2: Tests Menu\n"
                           ))
    if len(functions) >= int(choice / 10) and choice > 0:
        func = functions[choice if choice < 10 else int(choice / 10)]
        func(choice % 10)


if __name__ == '__main__':
    init(index=Index())
