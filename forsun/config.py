# -*- coding: utf-8 -*-
# 15/6/27
# create by: snower

__config = {}

DEFAULT_CONFIG = {
    "LOG_FILE": "/var/log/funsun.log",
    "LOG_LEVEL": "ERROR",
    "LOG_FORMAT": "",

    "BIND_ADDRESS": "0.0.0.0",
    "PORT": 5643,

    "STORE_DRIVER": "redis",
    "STORE_REDIS_HOST": "127.0.0.1",
    "STORE_REDIS_PORT": 6379,
    "STORE_REDIS_DB": 0,
    "STORE_REDIS_PREFIX": "forsun",
    "STORE_REDIS_SERVER_ID": "0",
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