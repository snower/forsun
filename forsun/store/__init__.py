# -*- coding: utf-8 -*-
# 15/6/8
# create by: snower

from .. import config
from .drivers.redis import RedisStore

class UnknownStoreDriverError(Exception):
    pass

def get_store(*args, **kwargs):
    driver = config.get("STORE_DRIVER", "redis")
    if driver == "redis":
        return RedisStore(*args, **kwargs)
    raise UnknownStoreDriverError()