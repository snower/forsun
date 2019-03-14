# -*- coding: utf-8 -*-
# 18/1/25
# create by: snower

import os
import time
import logging
import math
from collections import defaultdict
from tornado.ioloop import IOLoop
import msgpack
from tornado import gen
from ...plan import Plan
from ..store import Store
from ...utils import unicode_type
from ... import config

class MemStore(Store):
    def __init__(self, *args, **kwargs):
        super(MemStore, self).__init__(*args, **kwargs)

        self.ioloop = IOLoop.current()
        self.plans = {}
        self.time_plans = defaultdict(dict)
        self.current_time = int(time.mktime(time.gmtime()))
        self.store_file = config.get("STORE_MEM_STORE_FILE", "")
        if not self.store_file:
            self.store_file = os.path.join(os.path.expanduser('~'), ".forsun.dump")
        self.store_file = os.path.abspath(self.store_file)
        self.store_time_rate = config.get("STORE_MEM_TIME_RATE", 1)
        self.store_waited = False

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

                current_time = data.get(b"current_time")
                self.current_time = current_time if current_time and current_time > 0 else self.current_time
            logging.info("store mem load session %s", self.store_file)
        except Exception as e:
            logging.error("store mem load session error: %s %s", self.store_file, e)

    def store(self, saved_current_time = False):
        try:
            with open(self.store_file, "wb") as fp:
                data = msgpack.dumps({
                    b"plans": [plan.dumps() for key, plan in self.plans.items()],
                    b"time_plans": {ts: list(plans.keys()) for ts, plans in self.time_plans.items()},
                    b"current_time": self.current_time if saved_current_time else 0,
                })
                fp.write(data)

            if saved_current_time:
                logging.info("store mem save session %s", self.store_file)
        except Exception as e:
            logging.error("store mem save session error: %s %s", self.store_file, e)

    @gen.coroutine
    def uninit(self):
        self.store(True)

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

        if not self.store_waited:
            timeout = math.sqrt(len(self.plans)) * self.store_time_rate
            def on_store():
                self.store()
                self.store_waited = False
            self.ioloop.call_later(timeout, on_store)
            self.store_waited = True
        raise gen.Return(plan)

    @gen.coroutine
    def remove_plan(self, key):
        if key in self.plans:
            plan = self.plans.pop(key)

            if not self.store_waited:
                timeout = math.sqrt(len(self.plans)) * self.store_time_rate

                def on_store():
                    self.store()
                    self.store_waited = False

                self.ioloop.call_later(timeout, on_store)
                self.store_waited = True

            raise gen.Return(plan)
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
        status = self.time_plans[next_time].get(key, 0)
        raise gen.Return(status)

    @gen.coroutine
    def set_time_plan(self, next_time, key, status):
        last_status = self.time_plans[next_time].get(key, 0)
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
        prefix = prefix.rstrip("\n\t *")
        keys = []
        for key in self.plans:
            if key.startswith(prefix):
                keys.append(key)
        raise gen.Return(keys)