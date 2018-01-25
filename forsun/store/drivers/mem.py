# -*- coding: utf-8 -*-
# 18/1/25
# create by: snower

import time
from collections import defaultdict
from tornado import gen
from ..store import Store

class MemStore(Store):
    def __init__(self, *args, **kwargs):
        super(MemStore, self).__init__(*args, **kwargs)

        self.plans = {}
        self.time_plans = defaultdict(dict)
        self.current_time = int(time.time())

    @gen.coroutine
    def set_current(self, current_time):
        self.current_time = current_time
        raise gen.Return(self.current_time)

    @gen.coroutine
    def get_current(self):
        raise gen.Return(self.current_time)

    @gen.coroutine
    def set_plan(self, plan):
        self.plans[plan.key] = plan
        raise gen.Return(plan)

    @gen.coroutine
    def remove_plan(self, key):
        if key in self.plans:
            raise gen.Return(self.plans.pop(key))
        raise gen.Return(None)

    @gen.coroutine
    def get_plan(self, key):
        if key in self.plans:
            raise gen.Return(self.plans[key])
        raise gen.Return(None)

    @gen.coroutine
    def add_time_plan(self, plan):
        self.time_plans[plan.next_time][plan.key] = plan
        raise gen.Return(plan)

    @gen.coroutine
    def get_time_plan(self, ts):
        raise gen.Return(self.time_plans[ts].keys())

    @gen.coroutine
    def remove_time_plan(self, plan):
        if plan.key in self.time_plans[plan.next_time]:
            raise gen.Return(self.time_plans[plan.next_time].pop(plan.key))
        raise gen.Return(None)

    @gen.coroutine
    def delete_time_plan(self, ts):
        if ts in self.time_plans:
            raise gen.Return(self.time_plans.pop(ts))
        raise gen.Return(None)

    @gen.coroutine
    def get_plan_keys(self, prefix = ""):
        keys = []
        for key in self.plans:
            if key.startswith(prefix):
                keys.append(key)
        raise gen.Return(keys)