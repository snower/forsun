# -*- coding: utf-8 -*-
# 18/1/25
# create by: snower

import time
import logging
from collections import defaultdict
import msgpack
from tornado import gen
from ...plan import Plan
from ..store import Store
from ...utils import unicode_type
from ... import config

class MemStore(Store):
    def __init__(self, *args, **kwargs):
        super(MemStore, self).__init__(*args, **kwargs)

        self.plans = {}
        self.time_plans = defaultdict(dict)
        self.current_time = int(time.mktime(time.gmtime()))
        self.store_file = config.get("STORE_MEM_STORE_FILE", "/tmp/forsun.session")

        self.load()
        logging.info("use mem store %s", self.store_file)

    def load(self):
        try:
            with open(self.store_file, "rb") as fp:
                data = fp.read()
                data = msgpack.loads(data)
                self.plans = {}
                for plan in data.get(b"plans", []):
                    plan = Plan.loads(plan)
                    self.plans[plan.key] = plan

                self.time_plans = defaultdict(dict)
                for key, plans in data.get(b"time_plans", {}).items():
                    self.time_plans[key] = {}
                    for plan_key in (plans or []):
                        if not isinstance(plan_key, unicode_type):
                            plan_key = unicode_type(plan_key, "utf-8")

                        if plan_key in self.plans:
                            self.time_plans[key][plan_key] = self.plans[plan_key]

                self.current_time = data.get(b"current_time", self.current_time)
            logging.info("store mem load session %s", self.store_file)
        except Exception as e:
            logging.error("store mem load session error: %s %s", self.store_file, e)

    def unload(self):
        try:
            with open(self.store_file, "wb") as fp:
                data = msgpack.dumps({
                    b"plans": [plan.dumps() for key, plan in self.plans.items()],
                    b"time_plans": {ts: list(plans.keys()) for ts, plans in self.time_plans.items()},
                    b"current_time": self.current_time,
                })
                fp.write(data)
            logging.info("store mem save session %s", self.store_file)
        except Exception as e:
            logging.error("store mem save session error: %s %s", self.store_file, e)

    @gen.coroutine
    def uninit(self):
        self.unload()

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
    def add_time_plan(self, next_time, key):
        self.time_plans[next_time][key] = 0
        raise gen.Return(True)

    @gen.coroutine
    def get_time_plan(self, next_time, key):
        status = self.time_plans[next_time][key]
        raise gen.Return(status)

    @gen.coroutine
    def set_time_plan(self, next_time, key, status):
        last_status = self.time_plans[next_time][key]
        self.time_plans[next_time][key] = status
        raise gen.Return(last_status)

    @gen.coroutine
    def remove_time_plan(self, next_time, key):
        if key in self.time_plans[next_time]:
            raise gen.Return(self.time_plans[next_time].pop(key))
        raise gen.Return(None)

    @gen.coroutine
    def get_time_plans(self, ts):
        raise gen.Return(self.time_plans[ts].keys())

    @gen.coroutine
    def delete_time_plans(self, ts):
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