#!/usr/bin/env python3

import logging
import logging.handlers
import os

class Logger():
    '''
    Creates loggers for the various modules
    '''
    def __init__(self, log_path, log_level, log_to_file=False, quiet=False):
        self._format = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
        self._log_level = logging.getLevelName(log_level.upper())
        self._log_to_file = log_to_file
        self._log_path = log_path
        self._quiet = quiet

    def get_null_log(self, name):
        log = logging.getLogger(name)
        log.setLevel(self._log_level)
        nh = logging.NullHandler()
        nh.setFormatter(self._format)
        nh.setLevel(50)
        log.addHandler(nh)
        return log

    def get_log(self, name):
        log = logging.getLogger(name)
        log.setLevel(self._log_level)

        sh = logging.StreamHandler()
        sh.setFormatter(self._format)
        if self._quiet:
            sh.setLevel(50)
        log.addHandler(sh)

        if self._log_to_file:
            fh = logging.handlers.RotatingFileHandler(self._log_path, mode='a', maxBytes=1000000, backupCount=5)
            fh.setLevel(self._log_level)
            fh.setFormatter(self._format)
            log.addHandler(fh)

        return log