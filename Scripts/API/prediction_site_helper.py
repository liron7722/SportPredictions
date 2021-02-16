import gc
from pymongo.collection import ObjectId
from Scripts.Utility.db import DB
from Scripts.Analyzers.Handlers.Soccer.DataHandler import DataHandler as Dh
from Scripts.Predictor.Soccer.PredictorHandler import PredictorHandler as Ph


class Helper:
    version = "1.0.0"

    def __init__(self):
        gc.enable()
        self.data_handler = Dh()
        self.predictor_handler = Ph()
        self.db_client = DB('SOCCER')

    def load(self):
        db = self.db_client.get_db('Prediction-Site')
        competition_names = self.db_client.get_collections_names(db=db)
        for comp in competition_names:
            collection = self.db_client.get_collection(name=comp, db=db)
            fixtures = self.db_client.get_documents_list(collection=collection, fil={"Prediction": {'$exists': False}})
            for fixture in fixtures:
                self.handle_fixture(fixture, collection, comp)
                gc.collect()
            # TODO add another round with predictions with version different from class version
            # TODO Should update predictions if got new keys to predict or new models type
        gc.collect()

    def handle_fixture(self, fixture, collection, comp):
        try:
            info = {'competition': comp, 'home_team_name': fixture['Home Team'], 'away_team_name': fixture['Away Team'],
                    'home_team_manager': fixture['Home Manager'], 'away_team_manager': fixture['Away Manager'],
                    'ref': fixture['Referee']}
        except KeyError:
            info = {'competition': comp, 'home_team_name': fixture['Home Team'], 'home_team_manager': '',
                    'away_team_name': fixture['Away Team'], 'away_team_manager': '', 'ref': fixture['Referee']}
        fixture['Prediction'] = self.predict_db_fixture(info)
        fixture['Prediction_Version'] = self.version
        self.db_client.update_document(collection=collection, fil={'_id': ObjectId(fixture['_id'])}, data=fixture)
        gc.collect()

    def predict_db_fixture(self, fixture):
        def handle_game_data():
            fixture_info = {
                'Home Team': {'Name': fixture['home_team_name'], 'Manager': fixture['home_team_manager']},
                'Away Team': {'Name': fixture['away_team_name'], 'Manager': fixture['away_team_manager']},
                'Officials': [{'Name': fixture['ref']}]
            }
            return {'Score Box': fixture_info}

        comp_key = fixture['competition'].replace(' ', '-')
        fixture = handle_game_data()
        data = self.data_handler.get_fixture_data(info={'Competition': comp_key}, fixture=fixture)
        return self.predictor_handler.predict(comp_key=comp_key, data=data)
