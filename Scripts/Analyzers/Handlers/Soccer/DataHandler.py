from gc import collect
from Scripts.Utility.db import DB
from Scripts.Utility.logger import Logger
from Scripts.Utility.time import change_date_format, time_wrapper, call_sleep
from Scripts.Analyzers.Handlers.Soccer.Fixture import Fixture


class DataHandler:
    ENV = 'Development'

    def __init__(self):
        self.name = 'Soccer_Handler'
        self.logger = self.get_logger()
        self.db_client = self.get_db()

    def get_logger(self):
        return Logger(f'{self.name}.log').get_logger()

    def get_db(self):
        return DB(key='SOCCER', logger=self.logger)

    # Logger
    def log(self, message: str, level: int = 10):
        if self.logger is not None:
            if self.ENV == 'Development':
                level = 10
            elif self.ENV == 'Production':
                level = 20
            self.logger.log(level, message)

    def get_curr_season(self, comp_key):
        db = self.db_client.get_db(name=comp_key)
        season_names = self.db_client.get_collections_names(db=db)
        season_names.sort()
        return season_names[-1] if len(season_names) > 0 else '2020-2021'

    def get_fixture_data(self, info, fixture):
        info['Season'] = self.get_curr_season(info['Competition'])
        fixture['Score Box']['DateTime'] = {'Date': None}
        temp = Fixture(fixture=fixture, info=info, db=self.db_client, logger=self.logger)
        return temp.get_stats_for_prediction()

    # Load
    @time_wrapper
    def load_seasons(self, db, db_name, season_names):
        self.log(f'Cmd: load_seasons')
        season_names.sort()
        for coll_name in season_names:
            info = {'Competition': db_name, 'Season': coll_name}
            collection = self.db_client.get_collection(name=coll_name, db=db)  # get collection
            fixtures = self.db_client.get_documents_list(collection=collection)  # get all the documents
            # remove the basic info document
            for fixture in fixtures:
                if 'Season' in fixture.keys():
                    fixtures.remove(fixture)
                    break
            # change the date format to enable sort option
            for fixture in fixtures:
                date_value = fixture['Score Box']['DateTime']['Date']
                fixture['Score Box']['DateTime']['Date'] = change_date_format(date_value)
            # Sort fixture by date
            fixtures = sorted(fixtures, key=lambda f: f['Score Box']['DateTime']['Date'])
            # Handle fixture
            for fixture in fixtures:
                collect()  # Tell Garbage Collector to release unreferenced memory
                temp = Fixture(fixture=fixture, info=info, db=self.db_client, logger=self.logger)
                temp.run()
            collect()  # Tell Garbage Collector to release unreferenced memory

    # DB Load
    @time_wrapper
    def load_db(self):
        self.log(f'Cmd: load_db')
        competition_names = self.db_client.get_db_names()
        for key in ['admin', 'config', 'local', 'testing', 'Data-Handling', 'Prediction-Model',
                    'Big-5-European-Leagues']:
            if key in competition_names:
                competition_names.remove(key)  # pop utility db's
        for db_name in competition_names:
            db = self.db_client.get_db(name=db_name)  # get db
            season_names = self.db_client.get_collections_names(db=db)
            self.load_seasons(db, db_name, season_names)
            collect()  # Tell Garbage Collector to release unreferenced memory

    def run(self):
        self.log(f'Cmd: Data Handler run')
        while True:
            self.load_db()
            call_sleep(days=1)


if __name__ == '__main__':
    data_handler = DataHandler()
    data_handler.run()
