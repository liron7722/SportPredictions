from os import environ
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

DB_URI = environ.get('SPORT_PREDICTION_MONGO_DB_URI')


class DB:
    client = None
    db = None

    def __init__(self, logger=None):
        self.logger = logger
        self.get_connection()

    def get_connection(self):
        try:
            self.client = MongoClient(DB_URI)
            self.log('db establish connection')
        except ServerSelectionTimeoutError as _:
            message = 'db connection Timeout:\n' \
                      'For Cloud - check for if this machine ip is on whitelist\n' \
                      'For Local - check if the machine is running or if ports are blocked'
            self.logger.exception(message) if self.logger is not None else print(message)

    def get_db(self, name):
        self.db = self.client.get_database(name)
        self.log(f'got db: {name}')

    def get_collection(self, db, name):
        collection = db.get_collection(name)
        self.log(f'got collection: {name}')
        return collection

    def insert_document(self, collection, data):
        collection.insert_one(data)
        self.log('insert document to collection')

    def log(self, message):
        if self.logger is not None:
            self.logger.info(message)
