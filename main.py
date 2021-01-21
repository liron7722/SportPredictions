#!/usr/bin/env python3

import sys

# Scraper Imports
from Scripts.Scraper.SoccerScraper import SoccerScraper
# Analyzers Imports
from Scripts.Analyzers.Handlers.Soccer.DataHandler import DataHandler
# Models Imports
from Scripts.Predictor.Soccer.PredictorHandler import PredictorHandler

# Tests Imports
# Scraper Tests
# from Scripts.Testers.Scraper.Soccer.test_MatchReport import TestMatchReport
from Scripts.Testers.Scraper.Soccer.test_Season import TestSeason
# from Scripts.Testers.Scraper.Soccer.test_Competition import TestCompetition
# Analyzers Tests

# Models Tests


# Menu Functions
def run_soccer_scraper():
    soccer_scraper = SoccerScraper()
    soccer_scraper.run()


def run_data_handler():
    data_handler = DataHandler()
    data_handler.run()


def run_match_report_test():
    pass  # TestMatchReport().start()


def run_season_test():
    TestSeason().start()


def run_competition_test():
    pass  # TestCompetition().start()


def run_predictor_handler():
    predictor_handler = PredictorHandler()
    predictor_handler.run()


def menu():
    functions = {1: run_soccer_scraper,
                 2: run_data_handler,
                 3: run_predictor_handler,
                 4: run_match_report_test,
                 5: run_season_test,
                 6: run_competition_test
                 }
    if len(sys.argv) > 1:
        choice = int(sys.argv[1])

    else:
        choice = int(input("Enter which function you want to run:\n"
                           "1: run_soccer_scraper\n"
                           "2: run_data_handler\n"
                           "3: run_predictor_handler\n"
                           "4: run_match_report_test\n"
                           "5: run_season_test\n"
                           "6: run_competition_test\n"
                           ))

    if len(functions) >= choice > 0:
        functions[choice]()


if __name__ == '__main__':
    menu()
