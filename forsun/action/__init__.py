# -*- coding: utf-8 -*-
# 15/6/10
# create by: snower

import logging
import traceback
from tornado import gen
from .action import Action
from ..error import ActionExecuteRetry
from ..status import forsun_status

__drivers = None

class UnknownActionError(Exception):
    pass

def init_drivers():
    global __drivers
    __drivers = {}

    try:
        from .drivers import shellaction
        __drivers["shell"] = shellaction.ShellAction
        logging.info("action register shell %s", shellaction.ShellAction)
    except Exception as e:
        logging.error("load shell execute error: %s", e)

    try:
        from .drivers import httpaction
        __drivers["http"] = httpaction.HttpAction
        logging.info("action register http %s", httpaction.HttpAction)
    except Exception as e:
        logging.error("load http execute error: %s", e)

    try:
        from .drivers import redisaction
        __drivers["redis"] = redisaction.RedisAction
        logging.info("action register redis %s", redisaction.RedisAction)
    except Exception as e:
        logging.error("load redis execute error: %s", e)

    try:
        from .drivers import thriftaction
        __drivers["thrift"] = thriftaction.ThriftAction
        logging.info("action register thrift %s", thriftaction.ThriftAction)
    except Exception as e:
        logging.error("load thrift execute error: %s", e)

    try:
        from .drivers import beanstalkaction
        __drivers["beanstalk"] = beanstalkaction.BeanstalkAction
        logging.info("action register beanstalk %s", beanstalkaction.BeanstalkAction)
    except Exception as e:
        logging.error("load beanstalk execute error: %s", e)

    try:
        from .drivers import mysqlaction
        __drivers["mysql"] = mysqlaction.MysqlAction
        logging.info("action register mysql %s", mysqlaction.MysqlAction)
    except Exception as e:
        logging.error("load mysql execute error: %s", e)

def register_action(name, cls):
    if issubclass(cls, Action):
        __drivers[name] = cls
        logging.info("action register %s %s", name, cls)
        return True
    return False

def get_driver(action):
    if __drivers is None:
        init_drivers()
    try:
        driver = __drivers[action]
    except:
        raise UnknownActionError()
    return driver

def get_driver_names():
    if __drivers is None:
        return []
    return __drivers.keys()

@gen.coroutine
def execute(ts, plan):
    driver_cls = get_driver(plan.action)
    driver = driver_cls(ts, plan, plan.action, plan.params)
    try:
        yield driver.execute()
        succed = True
    except ActionExecuteRetry as e:
        raise e
    except Exception as e:
        forsun_status.action_executed_error_count += 1
        logging.error("action %s %s %s %s execute error: %s\n%s", plan.key, driver.action, driver.ts, driver.params, e, traceback.format_exc())
        succed = False
    raise gen.Return(succed)