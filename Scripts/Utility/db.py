from os import environ
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, DuplicateKeyError

DB_NAME = 'SPORT_PREDICTION_MONGO_DB_URI'


class DB:
    client = None

    def __init__(self, key, logger=None):
        self.key = key
        self.logger = logger
        self.get_connection()

    def get_connection(self):
        try:
            db_uri = environ.get(f'{self.key}_{DB_NAME}')  # get uri from environment variables
            self.client = MongoClient(db_uri)  # establish connection
            self.log('db establish connection')
        except ServerSelectionTimeoutError as _:
            message = 'db connection Timeout:\n' \
                      'For Cloud - check for if this machine ip is on whitelist\n' \
                      'For Local - check if the machine is running or if ports are blocked'
            self.logger.exception(message) if self.logger is not None else print(message)

    def get_db_names(self, key: str = 'name'):
        return [item[key] for item in self.client.list_databases()]

    @staticmethod
    def get_collections_names(db, key: str = 'name'):
        return [item[key] for item in db.list_collections()]

    @staticmethod
    def get_documents_list(collection, fil=None, sort='_id', ascending=1, limit=0, skip=0):
        fil = dict() if fil is None else fil
        return [item for item in collection.find(fil).sort(sort, ascending).limit(limit).skip(skip)]

    def get_db(self, name: str):
        db = self.client.get_database(name)
        self.log(f'got db: {name}')
        return db

    def get_collection(self, name: str, db):
        collection = db.get_collection(str(name))
        self.log(f'got collection: {name}')
        return collection

    def insert_document(self, collection, data: dict):
        ack = collection.insert_one(data)
        self.log('insert document to collection')
        return str(ack.inserted_id)

    def update_document(self, collection, fil: dict, data: dict):
        try:
            collection.update_one(fil, {"$set": data})
            self.log('updated document in the collection')
        except DuplicateKeyError:
            self.log('document is already in the collection')

    def is_document_exist(self, collection, fil: dict):
        cursor = collection.find(fil)
        try:
            cursor.next()
            flag = True
        except StopIteration:
            flag = False
        self.log(f'Document {"Not " * (not flag)}exist')
        return flag

    def log(self, message: str):
        if self.logger is not None:
            self.logger.debug(message)
        else:
            print(message)
