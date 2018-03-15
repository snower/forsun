# -*- coding: utf-8 -*-
# 15/6/10
# create by: snower

import os
import sys
import logging
import traceback
import threading
from tornado.ioloop import IOLoop
from tornado import gen
from .servers import Server
from . import store
from . import action
from . import timer
from . import log
from .extension import ExtensionManager
from . import config
from . import error

class Forsun(object):
    def __init__(self):
        log.init_config()
        self.ioloop = None
        self.read_event = threading.Event()
        self.store = None
        self.current_time = None

        store.init_stores()
        action.init_drivers()
        self.init_extensions()
        self.server = Server(self)

    @gen.coroutine
    def init(self):
        self.store = store.get_store()
        ExtensionManager.init()
        yield self.store.init()

    @gen.coroutine
    def uninit(self):
        yield self.store.uninit()
        ExtensionManager.uninit()

    def init_extensions(self):
        extension_path = config.get("EXTENSION_PATH", [])
        if extension_path:
            sys.path.append(extension_path)
            logging.info("register extension path %s", extension_path)

        extensions = config.get("EXTENSIONS", [])
        for extension in extensions:
            try:
                extension_module, extension_class = "".join(extension.split(".")[:-1]), extension.split(".")[-1]
                extension_module = __import__(extension_module, globals(), [], [extension_class])
                extension_class = getattr(extension_module, extension_class)
                ExtensionManager.add_extension(extension_class)
                logging.info("load extension %s %s", extension, extension_class)
            except Exception as e:
                logging.error("load extension error: %s %s", extension, e)

        ExtensionManager.register()

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
            yield self.store.remove_plan(plan.key)
            logging.debug("plan finish %s", plan.key)

    @gen.coroutine
    def handler_plan(self, ts, key):
        try:
            plan = yield self.store.get_plan(key)
            if plan:
                yield self.check_plan(ts, plan)
                self.ioloop.add_callback(self.execute_action, ts, plan)
        except Exception as e:
            logging.error("handler plan error: %s %s %s", ts, key, e)

    @gen.coroutine
    def handler(self, ts):
        try:
            plans = yield self.store.get_time_plan(ts)
            for key in plans:
                self.ioloop.add_callback(self.handler_plan, ts, key)
            yield self.store.delete_time_plan(ts)
        except Exception as e:
            logging.error("handler ts error: %s %s", ts, e)

    @gen.coroutine
    def check(self, ts):
        try:
            if self.current_time is None:
                self.current_time = yield self.store.get_current()
                logging.info("start by last time %s current time %s", self.current_time, timer.current())
                while self.current_time > 0 and self.current_time < ts:
                    yield self.handler(self.current_time)
                    self.current_time += 1
            self.current_time = ts
            yield self.store.set_current(self.current_time)
            yield self.handler(ts)
        except Exception as e:
            logging.error("check error: %s %s", ts, e)

    def time_out(self, ts):
        if self.ioloop:
            self.ioloop.add_callback(self.check, ts)

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
        try:
            def init():
                self.ioloop = IOLoop.current()
                self.ioloop.add_callback(self.init)
                self.ioloop.add_callback(logging.info, "forsun ready %s", os.getpid())
                self.read_event.set()

            self.server.start(init)
            self.read_event.wait()
            timer.start(self.time_out, self.exit)
            timer.loop()
        except KeyboardInterrupt:
            self.exit()

    def exit(self):
        @gen.coroutine
        def on_exit():
            yield self.uninit()
            self.server.stop()
            timer.stop()
            logging.info("stoped current time %s", timer.current())

        if self.ioloop is None:
            self.read_event.set()
            timer.stop()
        else:
            self.ioloop.add_callback(on_exit)
        logging.info("stoping")