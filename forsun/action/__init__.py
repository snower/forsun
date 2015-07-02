# -*- coding: utf-8 -*-
# 15/6/10
# create by: snower

import logging
import traceback
from tornado import gen
from drivers import shell, http

__drivers = None

class UnknownActionError(Exception):
    pass

def init_drivers():
    global __drivers
    __drivers = {
        "shell": shell.ShellAction,
        "http": http.HttpAction,
    }


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