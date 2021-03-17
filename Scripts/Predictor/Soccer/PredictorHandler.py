import gc
from os import environ
from Scripts.Utility.db import DB
from Scripts.Utility.logger import Logger
from Scripts.Predictor.Soccer.RFR import RFR


class PredictorHandler:
    ENV = environ.get('ENV') or 'Production'
    predictors = dict()

    def __init__(self):
        self.name = 'Predictor_Handler'
        gc.enable()
        self.logger = self.get_logger()
        self.db_client = self.get_db()
        self.load()

    def get_logger(self):
        return Logger(f'{self.name}', api=False)

    def get_db(self):
        return DB(key=f'SOCCER_SPORT_PREDICTION', logger=self.logger)

    def load(self):
        self.predictors['RFR'] = RFR(db=self.db_client, logger=self.logger)

    def predict(self, comp_key, data):
        result = dict()
        for key, predictor in self.predictors.items():
            result[key] = predictor.predict(comp_key=comp_key, data=data)
        return result

    def get_models_info(self):
        models = dict()
        for key, predictor in self.predictors.items():
            models[key] = dict()
            for comp_key in predictor.get_competition():
                models[key][comp_key] = list(predictor.get_prediction_key(comp_key))
        return models

    def get_comps_info(self):
        comps_info = dict()
        db = self.db_client.get_db('Data-Handling')
        competition_names = self.db_client.get_collections_names(db=db)

        # Init
        for col in ['Teams', 'Managers', 'Referees']:
            competition_names.remove(col)
        for comp in competition_names:
            comps_info[comp] = {'Teams': set(), 'Managers': set(), 'Referees': set()}

        # Append
        for col in ['Teams', 'Managers', 'Referees']:
            collection = self.db_client.get_collection(col, db)
            documents = self.db_client.get_documents_list(collection, fil={'Season': 'All Time'})
            for item in documents:
                name = item['Name']
                comp = item['Competition']
                comps_info[comp][col].add(name)

        for comp in comps_info.keys():
            for col in comps_info[comp].keys():
                comps_info[comp][col] = list(comps_info[comp][col])
        return comps_info

    def info(self):
        return {'Competitions': self.get_comps_info(),
                'Models': self.get_models_info()}

    def run(self):
        for key, predictor in self.predictors.items():
            self.logger.log(f'Running {key} Predictor create method', level=20)
            predictor.create()
