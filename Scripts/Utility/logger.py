#!/usr/bin/env python3

import logging
import logging.handlers
from .path import create_dir


class Logger:

    def __init__(self, name: str, path: str = None, logger=None):
        self.logger = self.start(name, path, logger)

    def get_logger(self):
        return self.logger

    # input - logName as string, logPath as string, logger as logging class
    # output - logger as logging class
    # do - set logger settings
    @staticmethod
    def start(log_name, log_path, logger=None):
        path = log_path if log_path is not None else ""
        name = log_name if log_name is not None else "NoName.log"
        new_logger = logging.getLogger(name) if logger is None else logger

        new_logger.setLevel(logging.DEBUG)  # level per system status
        msg = '%(asctime)s %(levelname)s %(module)s: %(message)s'
        formatter = logging.Formatter(msg, datefmt='%d-%m-%Y %H-%M-%S')

        # Stream Handler - cmd line
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        '''
        # File handler
        createDir(path)
        file_handler = logging.handlers.RotatingFileHandler(path + name, maxBytes=10485760, backupCount=10)
        file_handler.setFormatter(formatter)
        
        # adding Handlers
        new_logger.addHandler(file_handler)
        '''
        new_logger.addHandler(stream_handler)

        new_logger.info('Initialize Log')
        return new_logger
