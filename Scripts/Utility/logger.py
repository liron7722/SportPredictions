#!/usr/bin/env python3

import os
import requests
import logging
import logging.handlers
from json import dumps
from datetime import datetime
from Scripts.Utility.path import create_dir

ENV = os.environ.get('ENV') or 'Production'
ELASTIC_URL = os.environ.get('ELASTIC_URL') or 'http://localhost:9200/'
basedir = os.path.abspath(os.path.dirname(__file__))
BASE_PATH = f'{basedir}{os.sep}Logs{os.sep}'


class Logger:
    _name: str = None
    _logger: logging = None
    _elastic_flag: bool = False

    log_level_dict = {10: logging.getLevelName(10),
                      20: logging.getLevelName(20),
                      30: logging.getLevelName(30),
                      40: logging.getLevelName(40),
                      50: logging.getLevelName(50)}

    def __init__(self, name: str, path: str = None, logger=None, elastic: bool = True, api: bool = True):
        self._name = name
        self._elastic_flag = elastic
        # Create Elastic index
        self.elastic_initialize(api=api)
        self._logger = self.start(name, path) if logger is None else logger

    def get_logger(self):
        return self._logger

    # input - logName as string, logPath as string, logger as logging class
    # output - logger as logging class
    # do - set logger settings
    @staticmethod
    def start(log_name: str, log_path: str = None) -> logging:
        path = log_path if log_path is not None else BASE_PATH
        name = log_name if log_name is not None else "NoName.log"
        new_logger = logging.getLogger(name)

        # Initialize logger
        new_logger.setLevel(logging.DEBUG)  # level per system status
        msg = '%(asctime)s %(levelname)s %(module)s: %(message)s'

        formatter = logging.Formatter(msg, datefmt='%d-%m-%Y %H-%M-%S')

        # Stream Handler - cmd line
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        # File handler
        create_dir(path)
        file_handler = logging.handlers.RotatingFileHandler(path + name, maxBytes=10485760, backupCount=3)
        file_handler.setFormatter(formatter)

        # adding Handlers
        new_logger.addHandler(file_handler)
        new_logger.addHandler(stream_handler)

        new_logger.info('Initialize Log')
        return new_logger

    # Logs functions
    def log(self, message, level: int = 10):
        self.log_to_logger(message=dumps(message), level=level)
        self.log_to_elastic(message=message, level=level, exception=None)

    def log_to_logger(self, message: str, level: int = 10):
        if self._logger is not None:
            level = 20 if ENV == 'Production' and level == 10 else level
            self._logger.log(level, message)

    def log_to_elastic(self, message, level: int = 10, exception: Exception = None):
        headers = {'Content-Type': 'application/json'}
        if self._elastic_flag:
            dict_msg = {
                "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "level": self.log_level_dict[level] if level in self.log_level_dict.keys() else level,
                "message": message,
                "exception": exception}
            try:
                r = requests.post(url=f'{ELASTIC_URL}{self._name}/_doc/', data=dumps(dict_msg), headers=headers)
                print(f'log sent to Index {self._name}') if 200 <= r.status_code < 300 else print(
                    f'log was not sent to Index {self._name}')
            except requests.exceptions.ConnectionError:
                print('Elastic Server is down, could not send the log')

    # Elastic Handling functions
    def elastic_initialize(self, api: bool = True):
        try:
            self.elastic_create_index()
            self.elastic_index_mapping(api=api)
        except requests.exceptions.ConnectionError:
            print('Elastic Server is down, could not initialize')

    def elastic_create_index(self):
        r = requests.put(url=f'{ELASTIC_URL}{self._name}')
        if r.status_code == 200:
            print(f'Index {self._name} was created')
        elif r.status_code == 400:
            print(f'Index {self._name} was not created, reason: {r.json()["error"]["type"]}')
        else:
            print(f'Error occurred when trying to create index {self._name}')

    def elastic_index_mapping(self, api: bool = True):
        headers = {'Content-Type': 'application/json'}
        api_index_mapping = {
            "properties": {
                "level": {
                    "type": "keyword"
                },
                "message": {
                    "type": "nested",
                    "properties": {
                        'requested_function': {"type": "keyword"},
                        'method': {"type": "keyword"},
                        'user_agent': {"type": "keyword"},
                        'content_type': {"type": "keyword"},
                        'charset': {"type": "keyword"},
                        'url': {"type": "keyword"},
                        'remote_address': {"type": "keyword"}
                    }
                },
                "exception": {
                    "type": "text",
                    "fields": {
                        "raw": {
                            "type": "keyword"
                        }
                    }
                },
                "date": {
                    "type": "date",
                    "format": "yyyy-MM-dd HH:mm:ss"
                }
            }
        }
        default_index_mapping = {
            "properties": {
                "level": {
                    "type": "keyword"
                },
                "message": {
                    "type": "text",
                    "fields": {
                        "raw": {
                            "type": "keyword"
                        }
                    }
                },
                "exception": {
                    "type": "text",
                    "fields": {
                        "raw": {
                            "type": "keyword"
                        }
                    }
                },
                "date": {
                    "type": "date",
                    "format": "yyyy-MM-dd HH:mm:ss"
                }
            }
        }
        index_mapping = api_index_mapping if api else default_index_mapping
        r = requests.put(url=f'{ELASTIC_URL}{self._name}/_mapping', data=dumps(index_mapping), headers=headers)
        print(f'Index {self._name} was mapped') if r.status_code == 200 else print(f'Index {self._name} was not mapped')
