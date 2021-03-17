from os import environ
from gc import collect
from numpy import mean
from pandas import DataFrame
from pymongo import errors
from pickle import loads, dumps
from datetime import datetime as dt
from Scripts.Utility.db import DB
from Scripts.Utility.logger import Logger
from Scripts.Utility.json import encode_data, save


class Basic:
    ENV = environ.get('ENV') or 'Production'
    version = '1.1.0'
    model_type = 'Basic'

    logger: Logger = None
    db_client: DB = None

    x = None
    y = None
    models = dict()

    def __init__(self, db: DB = None, logger: Logger = None):
        self.db_client = db
        self.logger = logger
        self.logger.log(f'CMD: Initialize Predictor: {self.model_type}', level=20)

    # Getters
    def get_competition(self):
        return self.models.keys()

    def get_prediction_key(self, key):
        return self.models[key].keys()

    def predict(self, comp_key, data):
        self.logger.log(f'CMD: Predict\tPredictor: {self.model_type}\tCompetition: {comp_key}', level=20)
        data = DataFrame(data, index=[0]) if type(data) is dict else data
        for col in self.get_cols_to_drop():
            if col in data.columns:
                data = data.drop(col, axis=1)
        comp_key = 'All Competitions'
        result = {'Status': 'Failed',
                  'Reason': 'No models for these competition',
                  'Predictions': {}}
        if comp_key in self.models.keys():
            result['Status'] = 'Success'
            result['Reason'] = 'None'
            for key, item in self.models[comp_key].items():
                result['Predictions'][key] = {'Prediction': encode_data(item['Model'].predict(data)[0]),
                                              'Accuracy': item['Accuracy']}
        return result

    # Save
    def save_to_memory(self, comp_key, key, model, accuracy, cr):
        self.models[comp_key][key] = dict()
        self.models[comp_key][key]['Model'] = model
        self.models[comp_key][key]['Accuracy'] = accuracy
        self.models[comp_key][key]['CR'] = cr
        self.logger.log(f'{self.model_type} Model for {key} was created with {accuracy} accuracy', level=20)

    def save_to_db(self, comp_key, key, model, accuracy, cr):
        pickled_model = dumps(model)
        data = {'Name': key,
                'Model': pickled_model,
                # 'Parameters': model.best_params_,
                'Accuracy': accuracy,
                'CR': cr,
                'Type': self.model_type,
                'Version': self.version,
                'Created Time': dt.now()}

        db = self.db_client.get_db('Prediction-Model')
        collection = self.db_client.get_collection(comp_key, db)
        fil = {'Name': key, 'Type': self.model_type}  # Filter
        try:
            if self.db_client.is_document_exist(collection, fil):
                self.db_client.update_document(collection, fil, data)  # Update
            else:
                self.db_client.insert_document(collection, data)  # Insert
        except errors.DocumentTooLarge:
            save(data=data, name=f'{key}_{comp_key}_{self.model_type}_{self.version}', path=f'{self.model_type}_Models')

    # Load
    def load(self):
        self.logger.log(f'CMD: Load\tPredictor: {self.model_type}', level=20)
        db = self.db_client.get_db('Prediction-Model')
        competition_names = self.db_client.get_collections_names(db=db)
        for name in competition_names:
            if name == 'Parameters':
                continue
            self.logger.log(f'Inner CMD: Load Competition\tPredictor: {self.model_type}\tCompetition: {name}', level=20)
            # Load Competition
            collection = self.db_client.get_collection(name, db)
            documents = self.db_client.get_documents_list(collection)
            self.models[name] = dict()
            for item in documents:
                self.logger.log(f'Inner CMD: Load Models\tPredictor: {self.model_type}\tCompetition: {name}', level=20)
                # Load Models per prediction column
                key = item['Name']
                accuracy = item['Accuracy']
                cr = item['CR']
                pickled_model = item['Model']
                model = loads(pickled_model)
                self.save_to_memory(name, key, model, accuracy, cr)
        self.logger.log(f'CMD: Load\tPredictor: {self.model_type} is finished', level=20)

    def clear(self):
        self.x = None
        self.y = None
        collect()  # Tell Garbage Collector to release unreferenced memory

    # Create
    def create(self):
        db = self.db_client.get_db('Data-Handling')
        competition_names = self.db_client.get_collections_names(db=db)
        for col in ['Teams', 'Managers', 'Referees']:
            competition_names.remove(col)
        for name in competition_names:
            if name != 'Bundesliga':  # TODO drop after bug fix in data handling
                continue  # TODO Make models for all competitions together?
            self.logger.log(f'Inner CMD: Create Model\tPredictor: {self.model_type}\tCompetition: {name}', level=20)
            # Load Competition
            collection = self.db_client.get_collection(name, db)
            documents = self.db_client.get_documents_list(collection)
            self.prepare_data(documents)
            self.add_competition(name)
            self.clear()

    @staticmethod
    def get_cols_to_drop():
        return ['_id', 'Version', 'Competition', 'Season', 'Date', 'Attendance', 'Home Team', 'Away Team',
                'Home Manager', 'Away Manager', 'Referee', 'HT_XG', 'AT_XG', 'HT_CS_Date', 'AT_CS_Date',
                'HTM_CS_Date', 'ATM_CS_Date', 'HT_PS_Date', 'AT_PS_Date', 'HTM_PS_Date', 'ATM_PS_Date']

    def prepare_data(self, data):
        df = DataFrame(data)
        del data
        collect()  # clean memory
        for col in self.get_cols_to_drop():
            if col in df.columns:
                df = df.drop(col, axis=1)
        self.y = dict()
        # Drop rest of the prediction columns
        for col in df.columns:
            if 'Pre' in col:
                self.y[col] = df.pop(col).dropna()
        self.x = df

    def is_model_exist(self, comp_key, key):
        db = self.db_client.get_db('Prediction-Model')
        collection = self.db_client.get_collection(comp_key, db)
        documents = self.db_client.get_documents_list(collection, {'Name': key, 'Type': self.model_type})
        if len(documents) == 1:  # Check if item exist
            if documents[0]['Version'] == self.version:  # check item version
                return True  # item exist and up-to-date
        return False

    def add_competition(self, comp_key):
        self.models[comp_key] = dict()
        for key in self.y.keys():
            if self.is_model_exist(comp_key, key) is False:
                try:
                    self.add_model(comp_key, key)
                except TypeError:
                    self.logger.exception(f'Got TypeError at key: {key} in Competition: {comp_key}')

    def add_model(self, comp_key, key):
        self.logger.log(f'CMD: Predictor: {self.model_type}\tCompetition: {comp_key}\tModel: {key}', level=20)

    @staticmethod
    def get_default_parameters():
        pass

    def get_parameters(self, key):
        db = self.db_client.get_db('Prediction-Model')
        collection = self.db_client.get_collection('Parameters', db)
        fil = {'Name': key, 'Type': self.model_type}  # Filter
        documents = self.db_client.get_documents_list(collection, fil=fil)
        if len(documents) == 1:
            return documents[0]['Parameters']

        return self.get_default_parameters()

    def save_parameters(self, key, parameters):
        data = {'Name': key,
                'Parameters': parameters,
                'Type': self.model_type,
                'Version': self.version,
                'Created Time': dt.now()}

        db = self.db_client.get_db('Prediction-Model')
        collection = self.db_client.get_collection('Parameters', db)
        fil = {'Name': key, 'Type': self.model_type}  # Filter
        if self.db_client.is_document_exist(collection, fil):
            self.db_client.update_document(collection, fil, data)  # Update
        else:
            self.db_client.insert_document(collection, data)  # Insert

    @staticmethod
    def evaluate(model, test_features, test_labels):
        predictions = model.predict(test_features)
        model_errors = abs(predictions - test_labels)
        map_e = 100 * mean(model_errors / test_labels)
        accuracy = 100 - map_e
        print('Model Performance')
        print('Average Error: {:0.4f} degrees.'.format(mean(model_errors)))
        print('Accuracy = {:0.2f}%.'.format(accuracy))

        return accuracy
