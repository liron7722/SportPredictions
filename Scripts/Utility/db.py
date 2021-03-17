from os import environ
from Scripts.Utility.logger import Logger
from pymongo import MongoClient
from pymongo.mongo_client import database
from pymongo.errors import ServerSelectionTimeoutError, DuplicateKeyError

DB_NAME = 'SPORT_PREDICTION'


class DB:
    client: MongoClient = None
    logger: Logger = None

    def __init__(self, key: str, logger: Logger = None):
        self.key = key
        self.logger = logger
        self.get_connection()

    def get_connection(self):
        try:
            db_uri = environ.get(f'{self.key}_MONGO_DB_URI')  # get uri from environment variables
            self.client = MongoClient(db_uri)  # establish connection
            self.log('db establish connection')
        except ServerSelectionTimeoutError as _:
            message = 'db connection Timeout:\n' \
                      'For Cloud - check for if this machine ip is on whitelist\n' \
                      'For Local - check if the machine is running or if ports are blocked'
            self.logger.log(message, level=40) if self.logger is not None else print(message)

    def get_db_names(self, key: str = 'name') -> list:
        return [item[key] for item in self.client.list_databases()]

    @staticmethod
    def get_collections_names(db: database.Database, key: str = 'name') -> list:
        return [item[key] for item in db.list_collections()]

    @staticmethod
    def get_documents_list(collection: database.Collection, fil: dict = None, sort: str = '_id', ascending: int = 1,
                           limit: int = 0, skip: int = 0) -> list:
        fil = dict() if fil is None else fil
        return [item for item in collection.find(fil).sort(sort, ascending).limit(limit).skip(skip)]

    def get_db(self, name: str) -> database.Database:
        db = self.client.get_database(name)
        self.log(f'got db: {name}')
        return db

    def get_collection(self, name: str, db: database.Database) -> database.Collection:
        collection = db.get_collection(str(name))
        self.log(f'got collection: {name}')
        return collection

    def insert_document(self, collection: database.Collection, data: dict) -> str:
        ack = collection.insert_one(data)
        self.log('insert document to collection')
        return str(ack.inserted_id)

    def update_document(self, collection: database.Collection, fil: dict, data: dict):
        try:
            collection.update_one(fil, {"$set": data})
            self.log('updated document in the collection')
        except DuplicateKeyError:
            self.log('document is already in the collection')

    def is_document_exist(self, collection: database.Collection, fil: dict) -> bool:
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
            self.logger.log(message=message, level=10)
        else:
            print(message)
