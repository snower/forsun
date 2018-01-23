# -*- coding: utf-8 -*-
# 15/6/27
# create by: snower

from logging import config as logging_config
from . import config

def init_config():
    log_file = config.get("LOG_FILE", "/var/log/funsun.log")
    log_level = config.get("LOG_LEVEL", "INFO")

    log_config={
        "version":1,
        "formatters":{
            "main":{
                "format":'%(asctime)s %(process)d %(levelname)s %(message)s',
            }
        },
        "handlers": {
            "main":{
                'level': log_level,
                'class': 'logging.FileHandler',
                'formatter': 'main',
                'filename': log_file,
            }
        },
        "loggers": {
            "":{
                'handlers': ['main'],
                'level': log_level
            },
            "tornado.application":{
                'handlers': ['main'],
                'level': log_level
            },
            "tornado.general":{
                'handlers': ['main'],
                'level': log_level
            },
        }
    }

    logging_config.dictConfig(log_config)