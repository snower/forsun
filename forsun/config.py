# -*- coding: utf-8 -*-
# 15/6/27
# create by: snower

__config = {}

DEFAULT_CONFIG = {
    "LOG_FILE": "/var/log/funsun.log",
    "LOG_LEVEL": "INFO",
    "LOG_FORMAT": "",

    "STORE_DRIVER": "redis",
    "STORE_REDIS_HOST": "127.0.0.1",
    "STORE_REDIS_PORT": 3309,
    "STORE_REDIS_DB": 1,
    "STORE_REDIS_PREFIX": "forsun",
    "STORE_REDIS_SERVER_ID": "",

    "SERVER_DRIVER": "thrift",
    "SERVER_THRIFT_BIND_ADDRESS": "127.0.0.1",
    "SERVER_THRIFT_PORT": 5643,
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