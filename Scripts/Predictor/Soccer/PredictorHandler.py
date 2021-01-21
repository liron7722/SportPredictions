from Scripts.Utility.db import DB
from Scripts.Utility.logger import Logger
from Scripts.Predictor.Soccer.RFR import RFR


class PredictorHandler:
    ENV = 'Development'
    predictors = dict()

    def __init__(self):
        self.name = 'Predictor_Handler'
        self.logger = self.get_logger()
        self.db_client = self.get_db()
        self.load()

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

    def load(self):
        self.predictors['RFR'] = RFR(db=self.db_client, logger=self.logger)

    def predict(self, comp_key, data):
        result = dict()
        for key, predictor in self.predictors.items():
            result[key] = predictor.predict(comp_key=comp_key, data=data)
        return result

    def info(self):
        result = dict()
        for key, predictor in self.predictors.items():
            result[key] = dict()
            for comp_key in predictor.get_competition():
                result[key][comp_key] = list(predictor.get_prediction_key(comp_key))
        return result

    def run(self):
        for key, predictor in self.predictors.items():
            self.log(f'Running {key} Predictor create method')
            predictor.create()
