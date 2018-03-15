# -*- coding: utf-8 -*-
# 15/6/27
# create by: snower

from logging import config as logging_config
from . import config

def init_config():
    log_file = config.get("LOG_FILE", "/var/log/funsun.log")
    log_level = config.get("LOG_LEVEL", "INFO")

    if log_file == '-':
        main_handler = {
            'level': log_level,
            'class': 'logging.StreamHandler',
            'formatter': 'main',
        }
    else:
        main_handler = {
            'level': log_level,
            'class': 'logging.FileHandler',
            'formatter': 'main',
            'filename': log_file,
        }

    log_config={
        "version":1,
        "formatters": {
            "main": {
                "format":'%(asctime)s %(process)d %(levelname)s %(message)s',
            }
        },
        "handlers": {
            "main": main_handler,
        },
        "loggers": {
            "": {
                'handlers': ['main'],
                'level': log_level
            },
            "tornado.application": {
                'level': log_level
            },
            "tornado.general": {
                'level': log_level
            },
            "tornado.access": {
                'level': log_level
            },
            "tornadis.pool": {
                'handlers': ['main'],
                'level': "WARNING"
            },
            "tornadis.client": {
                'handlers': ['main'],
                'level': "WARNING"
            },
            "tornadis.connection": {
                'handlers': ['main'],
                'level': "WARNING"
            },
        }
    }

    logging_config.dictConfig(log_config)