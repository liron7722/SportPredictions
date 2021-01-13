#!/usr/bin/env python3

import os
import logging
import logging.handlers
from Scripts.Utility.path import create_dir

BASE_PATH = f"{os.path.dirname(os.path.realpath(''))}{os.sep}SportPredictions{os.sep}Logs{os.sep}"


class Logger:

    def __init__(self, name: str, path: str = None, logger=None):
        self.logger = self.start(name, path, logger)

    def get_logger(self):
        return self.logger

    # input - logName as string, logPath as string, logger as logging class
    # output - logger as logging class
    # do - set logger settings
    @staticmethod
    def start(log_name: str, log_path: str = None, logger=None):
        path = log_path if log_path is not None else BASE_PATH
        name = log_name if log_name is not None else "NoName.log"
        new_logger = logging.getLogger(name) if logger is None else logger

        new_logger.setLevel(logging.DEBUG)  # level per system status
        msg = '%(asctime)s %(levelname)s %(module)s: %(message)s'
        formatter = logging.Formatter(msg, datefmt='%d-%m-%Y %H-%M-%S')

        # Stream Handler - cmd line
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        # TODO add elastic stream

        # File handler
        create_dir(path)
        file_handler = logging.handlers.RotatingFileHandler(path + name, maxBytes=10485760, backupCount=3,
                                                            encoding="UTF-8")
        file_handler.setFormatter(formatter)
        
        # adding Handlers
        new_logger.addHandler(file_handler)
        new_logger.addHandler(stream_handler)

        new_logger.info('Initialize Log')
        return new_logger
