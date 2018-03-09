# -*- coding: utf-8 -*-
# 15/6/27
# create by: snower

import time
import logging
from tornado import gen
from ..plan import Plan
from .processor.ttypes import ForsunPlan, ForsunPlanError

class Handler(object):
    def __init__(self, forsun):
        self.forsun = forsun

    def to_eplan(self, plan):
        plan = ForsunPlan(
            is_time_out=plan.is_time_out,
            key=plan.key,
            second=plan.second,
            minute=plan.minute,
            hour=plan.hour,
            day=plan.day,
            month=plan.month,
            week=plan.week,
            next_time=plan.next_time,
            status=plan.status,
            count=plan.count,
            current_count=plan.current_count,
            action=plan.action,
            params=plan.params,
        )
        return plan

    @gen.coroutine
    def ping(self):
        raise gen.Return(0)

    @gen.coroutine
    def create(self, key, second, minute = -1, hour = -1, day = -1, month = -1, week = -1, action="shell", params={}):
        start_time = time.time()
        try:
            plan = Plan(key, second, minute, hour, day, month, week, is_time_out=False, action=action, params=params, created_time=time.mktime(time.gmtime()))
            yield self.forsun.create_plan(plan)
        finally:
            logging.debug("create %s %s %s %s %s %s %s %s %.2fms", key, second, minute, hour, day, month, week, action, (time.time() - start_time) * 1000)
        raise gen.Return(self.to_eplan(plan))

    @gen.coroutine
    def createTimeout(self, key, second, minute = -1, hour = -1, day = -1, month = -1, week = -1, count=0, action="shell", params={}):
        start_time = time.time()
        try:
            plan = Plan(key, second, minute, hour, day, month, week, is_time_out=True, count=count, action=action, params=params, created_time=time.mktime(time.gmtime()))
            yield self.forsun.create_plan(plan)
        finally:
            logging.debug("createTimeout %s %s %s %s %s %s %s %s %s %.2fms", key, second, minute, hour, day, month, week, count, action, (time.time() - start_time) * 1000)
        raise gen.Return(self.to_eplan(plan))

    @gen.coroutine
    def remove(self, key):
        start_time = time.time()
        try:
            plan = yield self.forsun.remove_plan(key)
        finally:
            logging.debug("remove %s %.2fms", key, (time.time() - start_time) * 1000)
        raise gen.Return(self.to_eplan(plan))

    @gen.coroutine
    def get(self, key):
        start_time = time.time()
        try:
            plan = yield self.forsun.get_pan(key)
        finally:
            logging.debug("get %s %.2fms", key, (time.time() - start_time) * 1000)
        raise gen.Return(self.to_eplan(plan))

    @gen.coroutine
    def getCurrent(self):
        start_time = time.time()
        try:
            current_ts = yield self.forsun.get_current_time()
            plans = yield self.forsun.get_time_plans(current_ts)
        finally:
            logging.debug("getCurrent %.2fms", (time.time() - start_time) * 1000)
        plans = [self.to_eplan(plan) for plan in plans]
        raise gen.Return(plans)

    @gen.coroutine
    def getTime(self, timestamp):
        start_time = time.time()
        try:
            plans = yield self.forsun.get_time_plans(timestamp)
        finally:
            logging.debug("getTime %.2fms", (time.time() - start_time) * 1000)
        plans = [self.to_eplan(plan) for plan in plans]
        raise gen.Return(plans)

    @gen.coroutine
    def getKeys(self, prefix=""):
        start_time = time.time()
        try:
            keys = yield self.forsun.get_keys(prefix)
        finally:
            logging.debug("getKeys %.2fms", (time.time() - start_time) * 1000)
        raise gen.Return(keys)