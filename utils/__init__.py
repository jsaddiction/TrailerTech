#!/usr/bin/env python3

import os
from utils.logger import Logger
from utils.config import Config
from utils.updater import Updater
from utils.environment import Env
from utils.arguments import get_arguments

__appName__ = 'TrailerTech'
__author__ = 'JsAddiction'
__version__ = '0.1.0'
__description__ = 'Download Trailers for your movie library.'

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'settings.ini')
LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'TrailerTech.log')
env = Env()
args = get_arguments(__appName__, __description__, __version__)
config = Config(CONFIG_PATH)
logger = Logger(LOG_PATH, config.log_level, config.log_to_file)
updater = Updater(logger.get_log('Updater'))
updater.pull(check_dev=True)
