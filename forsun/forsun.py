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
from servers import ThriftServer
import store
import action
import timer
import log
import config

class Forsun(object):
    def __init__(self):
        log.init_config()
        self.server = ThriftServer(self)
        self.store = store.get_store()

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
            yield self.store.store_plan(plan)
        else:
            yield self.store.remove_plan(plan)

    def time_out(self, ts):
        @gen.coroutine
        def handler():
            plans = yield self.store.get_time_plan(ts)
            for key in plans:
                plan = yield self.store.load_plan(key)
                if plan:
                    yield self.check_plan(ts, plan)
                    yield self.execute_action(ts, plan)

        IOLoop.current().add_callback(handler)

    @gen.coroutine
    def create_plan(self, plan):
        oplan = yield self.store.load_plan(plan.key)
        if oplan:
            yield self.store.remove_time_plan(oplan)
            yield self.store.remove_plan(oplan.key)
        if plan.next_time:
            yield self.store.add_time_plan(plan)
            res = yield self.store.add_plan(plan)
            logging.info("create plan %s", plan)
            raise gen.Return(res)
        raise gen.Return(False)

    @gen.coroutine
    def remove_plan(self, key):
        oplan = yield self.store.load_plan(key)
        if oplan:
            yield self.store.remove_time_plan(oplan)
            yield self.store.remove_plan(oplan.key)
            logging.info("remove plan %s", oplan)
            raise gen.Return(oplan)
        raise gen.Return(None)

    @gen.coroutine
    def get_pan(self, key):
        plan = yield self.store.load_plan(key)
        if plan:
            raise gen.Return(plan)
        raise gen.Return(None)

    @gen.coroutine
    def get_keys(self, prefix=""):
        keys = yield self.store.get_plan_keys(prefix)
        raise gen.Return(keys)

    @gen.coroutine
    def get_current_time(self):
        raise gen.Return(timer.current())

    @gen.coroutine
    def get_time_plans(self, ts):
        plans = yield self.store.get_time_plan(ts)
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