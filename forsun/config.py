# -*- coding: utf-8 -*-
# 15/6/27
# create by: snower

import os
from .utils import string_type, number_type

__config = {}

DEFAULT_CONFIG = {
    "LOG_FILE": "/var/log/funsun.log",
    "LOG_LEVEL": "ERROR",
    "LOG_FORMAT": "",

    "BIND_ADDRESS": "0.0.0.0",
    "PORT": 6458,

    "HTTP_BIND": "",

    "STORE_DRIVER": "mem",

    "STORE_MEM_STORE_FILE": "/tmp/forsun.session",

    "STORE_REDIS_HOST": "127.0.0.1",
    "STORE_REDIS_PORT": 6379,
    "STORE_REDIS_DB": 0,
    "STORE_REDIS_PREFIX": "forsun",
    "STORE_REDIS_SERVER_ID": 0,
    "STORE_REDIS_MAX_CONNECTIONS": 8,
    "STORE_REDIS_CLIENT_TIMEOUT": 7200,
    "STORE_REDIS_BULK_SIZE": 5,

    "ACTION_SHELL_CWD": "/tmp",
    "ACTION_HTTP_MAX_CLIENTS": 64,
    "ACTION_HTTP_CONNECT_TIMEOUT": 5,
    "ACTION_HTTP_REQUEST_TIMEOUT": 120,
    "ACTION_REDIS_MAX_CONNECTIONS": 8,
    "ACTION_REDIS_CLIENT_TIMEOUT": 7200,
    "ACTION_REDIS_BULK_SIZE": 5,
    "ACTION_THRIFT_MAX_CONNECTIONS": 64,
    "ACTION_MYSQL_USER": "root",
    "ACTION_MYSQL_PASSWD": "",
    "ACTION_MYSQL_MAX_CONNECTIONS": 8,
    "ACTION_MYSQL_WAIT_CONNECTION_TIMEOUT": 7200,
    "ACTION_MYSQL_IDLE_SECONDS": 120,

    "EXTENSION_PATH": "",
    "EXTENSIONS": [],
}

def get(name, default=None):
    return __config.get(name, default)

def set(name, value):
    old_value = __config[name]
    __config[name] = value
    return old_value

def update(config):
    __config.update(config)
    return __config

update(DEFAULT_CONFIG)
for key, value in DEFAULT_CONFIG.items():
    env_value = os.environ.get(key)
    if env_value is not None:
        try:
            if isinstance(value, number_type):
                set(key, int(env_value))
            elif isinstance(value, float):
                set(key, float(env_value))
            elif isinstance(value, string_type):
                set(key, str(env_value))
        except:pass