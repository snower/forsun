# -*- coding: utf-8 -*-
# 15/6/10
# create by: snower

import logging
import traceback
from tornado import gen

__drivers = None

class UnknownActionError(Exception):
    pass

def init_drivers():
    global __drivers
    __drivers = {}

    try:
        from .drivers import shellaction
        __drivers["shell"] = shellaction.ShellAction
    except Exception as e:
        logging.error("load shell execute error: %s", e)

    try:
        from .drivers import httpaction
        __drivers["http"] = httpaction.HttpAction
    except Exception as e:
        logging.error("load http execute error: %s", e)

    try:
        from .drivers import redisaction
        __drivers["redis"] = redisaction.RedisAction
    except Exception as e:
        logging.error("load redis execute error: %s", e)

    try:
        from .drivers import thrifaction
        __drivers["thrift"] = thrifaction.ThriftAction
    except Exception as e:
        logging.error("load thrift execute error: %s", e)

    try:
        from .drivers import beanstalkaction
        __drivers["beanstalk"] = beanstalkaction.BeanstalkAction
    except Exception as e:
        logging.error("load beanstalk execute error: %s", e)

def get_driver(action):
    if __drivers is None:
        init_drivers()
    try:
        driver = __drivers[action]
    except:
        raise UnknownActionError()
    return driver

@gen.coroutine
def execute(ts, plan):
    driver_cls = get_driver(plan.action)
    driver = driver_cls(ts, plan, plan.action, plan.params)
    try:
        yield driver.execute()
    except Exception as e:
        logging.error("action %s %s %s execute error: %s\n%s", driver.action, driver.ts, driver.params, e, traceback.format_exc())