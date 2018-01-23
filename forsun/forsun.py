# -*- coding: utf-8 -*-
# 15/6/10
# create by: snower

import os
import sys
import logging
import traceback
import signal
from tornado.ioloop import IOLoop
from tornado import gen
from .servers import ThriftServer
from . import store
from . import action
from . import timer
from . import log
from . import config
from . import error

class Forsun(object):
    def __init__(self):
        log.init_config()
        self.server = ThriftServer(self)
        self.store = store.get_store()
        self.current_time = None

        self.init_extensions()

    def init_extensions(self):
        extensions_path = config.get("EXTENSIONS_PATH", "")
        for ext in extensions_path.split(";"):
            if ext and os.path.exists(ext):
                sys.path.append(os.path.abspath(ext))

    @gen.coroutine
    def execute_action(self, ts, plan):
        try:
            yield action.execute(ts, plan)
        except Exception as e:
            logging.error("plan %s action execute error: %s\n", plan.key, e, traceback.format_exc())

    @gen.coroutine
    def check_plan(self, ts, plan):
        plan.last_timeout = ts
        plan.current_count += 1
        plan.next_time = plan.get_next_time()
        if plan.next_time:
            yield self.store.add_time_plan(plan)
            yield self.store.set_plan(plan)
        else:
            yield self.store.remove_plan(plan)
            logging.debug("plan finish %s", plan.key)

    def time_out(self, ts):
        @gen.coroutine
        def handler(ts):
            plans = yield self.store.get_time_plan(ts)
            for key in plans:
                plan = yield self.store.get_plan(key)
                if plan:
                    yield self.check_plan(ts, plan)
                    IOLoop.current().add_callback(self.execute_action, ts, plan)

        @gen.coroutine
        def check(ts):
            if self.current_time is None:
                self.current_time = yield self.store.get_current()
                while self.current_time > 0 and self.current_time < ts:
                    yield handler(self.current_time)
                    self.current_time += 1
            self.current_time = ts
            yield self.store.set_current(self.current_time)
            yield handler(ts)

        IOLoop.current().add_callback(check, ts)

    @gen.coroutine
    def create_plan(self, plan):
        oplan = yield self.store.get_plan(plan.key)
        if oplan:
            yield self.store.remove_time_plan(oplan)
            yield self.store.remove_plan(oplan.key)
        if not plan.next_time:
            raise error.WillNeverArriveTimeError()

        try:
            action.get_driver(plan.action)
        except action.UnknownActionError:
            raise error.UnknownActionError()

        yield self.store.add_time_plan(plan)
        res = yield self.store.set_plan(plan)
        if not res:
            raise error.StorePlanError

    @gen.coroutine
    def remove_plan(self, key):
        oplan = yield self.store.get_plan(key)
        if not oplan:
            raise error.NotFoundPlanError()

        yield self.store.remove_time_plan(oplan)
        yield self.store.remove_plan(oplan.key)
        raise gen.Return(oplan)

    @gen.coroutine
    def get_pan(self, key):
        plan = yield self.store.get_plan(key)
        if not plan:
            raise error.NotFoundPlanError()
        raise gen.Return(plan)

    @gen.coroutine
    def get_keys(self, prefix=""):
        keys = yield self.store.get_plan_keys(prefix)
        raise gen.Return(keys)

    @gen.coroutine
    def get_current_time(self):
        raise gen.Return(timer.current())

    @gen.coroutine
    def get_time_plans(self, ts):
        keys = yield self.store.get_time_plan(ts)
        plans = []
        for key in keys:
            plan = yield self.store.get_plan(key)
            if plan:
                plans.append(plan)
        raise gen.Return(plans)

    def serve(self):
        signal.signal(signal.SIGHUP, lambda signum,frame: self.exit())
        signal.signal(signal.SIGINT, lambda signum,frame: self.exit())
        signal.signal(signal.SIGTERM, lambda signum,frame: self.exit())
        try:
            self.server.start()
            timer.start(self.time_out)
            timer.loop()
        except KeyboardInterrupt:
            self.exit()

    def exit(self):
        self.server.stop()
        timer.stop()