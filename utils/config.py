#!/usr/bin/env python3

import os
import sys
import shutil
from configparser import ConfigParser

class Config(object):
    def __init__(self, configPath):
        self._raw_config = None
        self.path = configPath
        self.parse()

    def parse(self):
        if os.path.isfile(self.path):
            parser = ConfigParser()
            try:
                parser.read(self.path)
                self._raw_config = parser
            except Exception as e:
                print('Could not read settings.ini ERROR: {}'.format(e))
        else:
            print('Could not find the settings.ini file. Creating one using the example "settings.ini.example"')
            exampleFile = os.path.join(os.path.dirname(self.path), 'settings.ini.example')
            try:
                shutil.copyfile(exampleFile, self.path)
            except Exception:
                print('Could not create your settings file. Create it manually.')
            else:
                print('Please configure settings.ini and rerun this script.')

    @property
    def log_level(self):
        if not self._raw_config is None:
            if 'LOGS' in self._raw_config.sections():
                return self._raw_config['LOGS'].get('log_level', 'info')
        return 'info'

    @property
    def log_to_file(self):
        if not self._raw_config is None:
            if 'LOGS' in self._raw_config.sections():
                return self._raw_config['LOGS'].getboolean('log_to_file', False)
        return False

    @property
    def tmdb_API_key(self):
        if not self._raw_config is None:
            if 'TMDB' in self._raw_config.sections():
                return self._raw_config['TMDB'].get('api_key', '')
        return False

    @property
    def languages(self):
        if not self._raw_config is None:
            if 'TRAILERS' in self._raw_config.sections():
                langs = self._raw_config['TRAILERS'].get('languages').split(',')
                for lang in langs:
                    lang.strip
                return langs
        return []

    @property
    def min_resolution(self):
        if not self._raw_config is None:
            if 'TRAILERS' in self._raw_config.sections():
                return self._raw_config['TRAILERS'].getint('min_resolution', 0)
        return 0

    @property
    def max_resolution(self):
        if not self._raw_config is None:
            if 'TRAILERS' in self._raw_config.sections():
                return self._raw_config['TRAILERS'].getint('max_resolution', 4000)
        return 4000

    @property
    def youtube_enabled(self):
        if not self._raw_config is None:
            if 'YOUTUBE' in self._raw_config.sections():
                return self._raw_config['YOUTUBE'].getboolean('enabled', True)
        return True

    @property
    def apple_enabled(self):
        if not self._raw_config is None:
            if 'APPLE' in self._raw_config.sections():
                return self._raw_config['APPLE'].getboolean('enabled', True)
        return True