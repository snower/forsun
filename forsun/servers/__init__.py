# -*- coding: utf-8 -*-
# 15/6/10
# create by: snower

from .. import config
from drivers.thrift import ThriftServer

class UnknownServerDriverError(Exception):pass

def get_server(*args, **kwargs):
    driver = config.get("SERVER_DRIVER", "thrift")
    if driver == "thrift":
        return ThriftServer(*args, **kwargs)
    raise UnknownServerDriverError()