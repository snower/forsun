# -*- coding: utf-8 -*-
# 15/6/27
# create by: snower

import time
from tornado import gen
from ....plan import Plan
from .processor.ttypes import ForsunPlan, ForsunPlanError

class Handler(object):
    def __init__(self, crontab):
        self._crontab = crontab

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
    def create(self, key, second, minute = -1, hour = -1, day = -1, month = -1, week = -1, action="event", params="{}"):
        try:
            plan = Plan(key, second, minute, hour, day, month, week, is_time_out=False, action=action, params=params, created_time=time.time())
            res = yield self._crontab.create_plan(plan)
        except Exception as e:
            raise ForsunPlanError(1, str(e))
        if not res:
            raise ForsunPlanError(1, str(res))
        raise gen.Return(self.to_eplan(plan))

    @gen.coroutine
    def createTimeout(self, key, second, minute = -1, hour = -1, day = -1, month = -1, week = -1, count=0, action="event", params="{}"):
        try:
            plan = Plan(key, second, minute, hour, day, month, week, is_time_out=True, count=count, action=action, params=params, created_time=time.time())
            res = yield self._crontab.create_plan(plan)
        except Exception as e:
            raise ForsunPlanError(1, str(e))
        if not res:
            raise ForsunPlanError(1, str(res))
        raise gen.Return(self.to_eplan(plan))

    @gen.coroutine
    def remove(self, key):
        try:
            plan = yield self._crontab.remove_plan(key)
        except Exception as e:
            raise ForsunPlanError(1, str(e))
        if not plan:
            raise ForsunPlanError(1, "")
        raise gen.Return(self.to_eplan(plan))

    @gen.coroutine
    def get(self, key):
        try:
            plan = yield self._crontab.get_pan(key)
        except Exception as e:
            raise ForsunPlanError(1, str(e))
        if not plan:
            raise ForsunPlanError(1, "")
        raise gen.Return(self.to_eplan(plan))