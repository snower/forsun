# -*- coding: utf-8 -*-
# 15/6/27
# create by: snower

from logging import config as logging_config
from . import config


def init_config():
    log_file = config.get("LOG_FILE", "/var/log/funsun.log")
    log_level = config.get("LOG_LEVEL", "INFO")
    log_format = config.get("LOG_FORMAT", "%(asctime)s %(process)d %(levelname)s %(message)s")
    log_rotate = config.get("LOG_ROTATE", "")
    log_backup_Count = config.get("LOG_BACKUP_COUNT", 64)

    if log_file == '-':
        main_handler = {
            'level': log_level,
            'class': 'logging.StreamHandler',
            'formatter': 'main',
        }
    else:
        if log_rotate == "DAY":
            main_handler = {
                'level': log_level,
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'formatter': 'main',
                'filename': log_file,
                'when': "MIDNIGHT",
                'backupCount': log_backup_Count,
            }
        else:
            units = {"B": 1, "K": 1024, "M": 1024 * 1024, "G": 1024 * 1024 * 1024}
            file_bytes = 0

            if log_rotate and log_rotate[-1] in units:
                try:
                    file_bytes = int(float(log_rotate[:-1]) * units[log_rotate[-1]])
                except: pass

            if file_bytes:
                main_handler = {
                    'level': log_level,
                    'class': 'logging.handlers.RotatingFileHandler',
                    'formatter': 'main',
                    'filename': log_file,
                    'maxBytes': file_bytes,
                    'backupCount': log_backup_Count,
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
                "format": log_format,
            }
        },
        "handlers": {
            "logger": main_handler,
        },
        "loggers": {
            "": {
                'handlers': ['logger'],
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
                'handlers': ['logger'],
                'level': "WARNING"
            },
            "tornadis.client": {
                'handlers': ['logger'],
                'level': "WARNING"
            },
            "tornadis.connection": {
                'handlers': ['logger'],
                'level': "WARNING"
            },
        }
    }

    logging_config.dictConfig(log_config)