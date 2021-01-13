import gc
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

    # Load
    @time_wrapper
    def load_seasons(self, db, db_name, season_names):
        self.log(f'Cmd: load_seasons')
        season_names.sort()
        for coll_name in season_names:
            info = {'Competition': db_name, 'Season': coll_name}
            collection = self.db_client.get_collection(name=coll_name, db=db)  # get collection
            fixtures = self.db_client.get_documents_list(collection=collection)  # get all the documents
            for fixture in fixtures:
                if 'Season' in fixture.keys():  # skip the basic info document
                    temp = fixture
                    continue
                else:  # change the date format to enable sort option
                    date_value = fixture['Score Box']['DateTime']['Date']
                    fixture['Score Box']['DateTime']['Date'] = change_date_format(date_value)
            fixtures.remove(temp)
            fixtures = sorted(fixtures, key=lambda f: f['Score Box']['DateTime']['Date'])
            for fixture in fixtures:
                gc.collect()  # Tell Garbage Collector to release unreferenced memory
                temp = Fixture(fixture=fixture, info=info, db=self.db_client, logger=self.logger)
                temp.run()
            gc.collect()  # Tell Garbage Collector to release unreferenced memory

    # DB Load
    @time_wrapper
    def load_db(self):
        self.log(f'Cmd: load_db')
        competition_names = self.db_client.get_db_names()
        for key in ['admin', 'config', 'local', 'testing', 'Data-Handling', 'Big-5-European-Leagues']:
            if key in competition_names:
                competition_names.remove(key)  # pop utility db's
        for db_name in competition_names:
            db = self.db_client.get_db(name=db_name)  # get db
            season_names = self.db_client.get_collections_names(db=db)
            self.load_seasons(db, db_name, season_names)
            gc.collect()  # Tell Garbage Collector to release unreferenced memory

    def run(self):
        self.log(f'Cmd: Data Handler run')
        while True:
            self.load_db()
            call_sleep(days=1)


if __name__ == '__main__':
    data_handler = DataHandler()
    data_handler.run()
