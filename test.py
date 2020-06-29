import os
import unittest
import logging
import logging.config
import yaml

with open('logger.yaml', 'r') as f:
    config = yaml.safe_load(f.read())
    # manually set loglevel for tests to DEBUG
    # config['root']['level'] = 'DEBUG'
    # for k,v in config['loggers'].items():
    #     config['loggers'][k]['level'] = 'DEBUG'
    logging.config.dictConfig(config)

#this stops automator from calling os.system commands!!!!
os.environ['SILVIUX_ENV'] = 'test'

#import functions named test_* for unittest.main()
from silviux.test.test import *
from silviux.test.test_middleware import *

unittest.main()
