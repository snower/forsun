# -*- coding: utf-8 -*-
# 15/6/8
# create by: snower

import logging
from .. import config
from .store import Store

class UnknownStoreDriverError(Exception):
    pass

__stores = {}

def init_stores():
    try:
        from .drivers.mem import MemStore
        __stores['mem'] = MemStore
        logging.info("store register mem %s", MemStore)
    except Exception as e:
        logging.error("store load mem error: %s", e)

    try:
        from .drivers.redis import RedisStore
        __stores['redis'] = RedisStore
        logging.info("store register redis %s", RedisStore)
    except Exception as e:
        logging.error("store load redis error: %s", e)

def register_store(name, cls):
    if issubclass(cls, Store):
        __stores[name] = cls
        logging.info("store register %s %s", name, cls)
        return True
    return False

def get_store(*args, **kwargs):
    driver = config.get("STORE_DRIVER", "mem")
    if not __stores:
        init_stores()

    if driver not in __stores:
        raise UnknownStoreDriverError()
    return __stores[driver](*args, **kwargs)

def get_store_names():
    return __stores.keys()