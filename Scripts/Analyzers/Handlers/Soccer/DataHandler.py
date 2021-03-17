from os import environ
from gc import collect
from Scripts.Utility.db import DB
from Scripts.Utility.logger import Logger
from Scripts.Utility.time import change_date_format, time_wrapper, call_sleep
from Scripts.Analyzers.Handlers.Soccer.Fixture import Fixture


class DataHandler:
    ENV = environ.get('ENV') or 'Production'
    logger: Logger = None
    db_client: DB = None

    def __init__(self):
        self.name = 'Soccer_Handler'
        self.logger = Logger(f'{self.name}', api=False)
        self.db_client = DB(key=f'SOCCER_SPORT_PREDICTION', logger=self.logger)

    def get_curr_season(self, comp_key: str):
        db = self.db_client.get_db(name=comp_key)
        season_names = self.db_client.get_collections_names(db=db)
        season_names.sort()
        return season_names[-1] if len(season_names) > 0 else '2020-2021'

    def get_fixture_data(self, info: dict, fixture: dict):
        info['Season'] = self.get_curr_season(info['Competition'])
        fixture['Score Box']['DateTime'] = {'Date': None}
        match = Fixture(fixture=fixture, info=info, db=self.db_client, logger=self.logger)
        return match.get_stats_for_prediction()

    # Load
    @time_wrapper
    def load_seasons(self, db, db_name, season_names, output_coll):
        self.logger.log(f'Cmd: load_seasons', level=10)
        season_names.sort()
        for season in season_names:
            count = 1
            self.logger.log(f'handling season {season}', level=10)
            info = {'Competition': db_name, 'Season': season}
            collection = self.db_client.get_collection(name=season, db=db)  # get collection
            sort_key = "Score Box.DateTime.Date"  # sort by date
            fixtures = self.db_client.get_documents_list(collection=collection, sort=sort_key, skip=0)  # get fixtures
            # Handle fixture
            for fixture in fixtures:
                self.logger.log(f'handling fixture no: {count}', level=10)
                try:
                    date_value = fixture['Score Box']['DateTime']['Date']
                    fixture['Score Box']['DateTime']['Date'] = change_date_format(date_value)
                    temp = Fixture(fixture=fixture, info=info, coll=output_coll, db=self.db_client, logger=self.logger)
                    temp.run()
                except Exception:
                    self.logger.log(f'Got New error in data handling process comp: {db_name}\tseason: {season}\t'
                                    f'no: {count}', level=50)
                finally:
                    count += 1
                    collect()  # Tell Garbage Collector to release unreferenced memory
            collect()  # Tell Garbage Collector to release unreferenced memory

    # DB Load
    @time_wrapper
    def load_db(self):
        self.logger.log(f'Cmd: load_db', level=10)
        competition_names = self.db_client.get_db_names()
        for key in ['admin', 'config', 'local', 'testing', 'Data-Handling', 'Prediction-Model', 'Prediction-Site',
                    'Big-5-European-Leagues']:
            if key in competition_names:
                competition_names.remove(key)  # pop utility db's
        output_db = self.db_client.get_db(name='Data-Handling')
        for db_name in competition_names:
            output_coll = self.db_client.get_collection(name=db_name, db=output_db)
            db = self.db_client.get_db(name=db_name)  # get db
            season_names = self.db_client.get_collections_names(db=db)
            self.load_seasons(db, db_name, season_names, output_coll)
            collect()  # Tell Garbage Collector to release unreferenced memory

    def run(self):
        self.logger.log(f'Cmd: Data Handler run', level=20)
        while True:
            self.load_db()
            call_sleep(minutes=10)


if __name__ == '__main__':
    data_handler = DataHandler()
    data_handler.run()
