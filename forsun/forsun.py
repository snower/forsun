# -*- coding: utf-8 -*-
# 15/6/10
# create by: snower

import os
import sys
import time
import logging
import traceback
import threading
from tornado.ioloop import IOLoop
from tornado import gen
from .servers.server import Server
from .plan import Plan
from . import store
from . import action
from . import timer
from . import log
from .extension import ExtensionManager
from . import config
from . import error
from .status import forsun_status

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
        logging.info("use store %s %s", config.get("STORE_DRIVER", "mem"), self.store)

        ExtensionManager.init()
        yield self.store.init()
        logging.info("inited")

    @gen.coroutine
    def uninit(self):
        yield self.store.uninit()
        ExtensionManager.uninit()
        logging.info("uninited")

    def init_extensions(self):
        extension_path = config.get("EXTENSION_PATH", '')
        if extension_path:
            sys.path.append(extension_path)
            logging.info("register extension path %s", extension_path)

        extensions = config.get("EXTENSIONS", [])
        for extension in extensions:
            try:
                extension_module, extension_class = "".join(extension.split(".")[:-1]), extension.split(".")[-1]
                extension_module = extension_module if isinstance(extension_module, str) else extension_module.encode("utf-8")
                extension_class = extension_class if isinstance(extension_class, str) else extension_class.encode("utf-8")
                extension_module = __import__(extension_module, globals(), [], [extension_class])
                extension_class = getattr(extension_module, extension_class)
                ExtensionManager.add_extension(extension_class)
                logging.info("load extension %s %s", extension, extension_class)
            except Exception as e:
                logging.error("load extension error: %s %s", extension, e)

        ExtensionManager.register()

    @gen.coroutine
    def retry_plan(self, plan):
        try:
            if "_:_retry" in plan.key:
                retry_count = plan.current_count
                key = plan.key
            else:
                retry_count = 1
                key = plan.key + ":_:_retry"

            if retry_count <= config.get("ACTION_RETRY_MAX_COUNT", 0):
                delay_seconds = config.get("ACTION_RETRY_DELAY_SECONDS", 3)
                delay_time = delay_seconds + delay_seconds * config.get("ACTION_RETRY_DELAY_RATE", 1) * retry_count
                delay_plan = Plan(key, delay_time, is_time_out=True, count=1, action=plan.action, params=plan.params, created_time=time.mktime(time.gmtime()))
                delay_plan.current_count = retry_count
                yield self.create_plan(delay_plan)
                forsun_status.action_retried_count += 1
        except Exception as e:
            logging.error("plan %s retry error: %s\n%s", plan.key, e, traceback.format_exc())

    @gen.coroutine
    def execute_action(self, ts, plan, status_expried):
        try:
            forsun_status.action_executing_count += 1
            succed = yield action.execute(ts, plan)
        except error.ActionExecuteRetry:
            forsun_status.action_executed_error_count += 1
            yield self.retry_plan(plan)
            succed = False
        except Exception as e:
            forsun_status.action_executed_error_count += 1
            logging.error("plan %s action execute error: %s\n%s", plan.key, e, traceback.format_exc())
            succed = False
        finally:
            forsun_status.action_executing_count -= 1
            forsun_status.action_executed_count += 1

        if status_expried:
            try:
                yield self.store.set_time_plan(ts, plan.key, 1 if succed else -1)
            except Exception as e:
                logging.error("save status error: %s", e)

    @gen.coroutine
    def check_plan(self, ts, plan):
        plan.last_timeout = ts
        plan.current_count += 1
        plan.next_time = plan.get_next_time()
        if plan.next_time:
            yield self.store.add_time_plan(plan.next_time, plan.key)
            yield self.store.set_plan(plan)

    @gen.coroutine
    def handler_plan_expried(self, ts, key):
        try:
            plan = yield self.store.get_plan(key)
            if plan:
                if (not plan.next_time or plan.next_time == ts):
                    yield self.store.remove_plan(plan.key)
                    forsun_status.plan_count -= 1
                    logging.debug("plan finish %s", plan.key)
            else:
                logging.warning("handler plan: %s %s not found", ts, key)
        except Exception as e:
            logging.error("handler plan expried error: %s %s %s", ts, key, e)

    @gen.coroutine
    def handler_expried(self, ts):
        try:
            plans = yield self.store.get_time_plans(ts)
            for key in plans:
                self.ioloop.add_callback(self.handler_plan_expried, ts, key)
            yield self.store.delete_time_plans(ts)
        except Exception as e:
            logging.error("handler ts expried error: %s %s", ts, e)

    @gen.coroutine
    def handler_plan(self, ts, key, status_expried):
        try:
            plan = yield self.store.get_plan(key)
            if plan:
                yield self.check_plan(ts, plan)
                if status_expried == 0 and not plan.next_time:
                    yield self.store.remove_plan(plan.key)
                    forsun_status.plan_count -= 1
                    logging.debug("plan finish %s", plan.key)

                self.ioloop.add_callback(self.execute_action, ts, plan, status_expried)
            else:
                logging.warning("handler plan: %s %s not found", ts, key)
        except Exception as e:
            logging.error("handler plan error: %s %s %s", ts, key, e)

    @gen.coroutine
    def handler(self, ts):
        try:
            status_expried = config.get("STORE_STATUS_EXPRIED", 0)

            forsun_status.timeout_handling_count += 1
            plans = yield self.store.get_time_plans(ts)
            for key in plans:
                self.ioloop.add_callback(self.handler_plan, ts, key, status_expried)

            if status_expried == 0:
                yield self.store.delete_time_plans(ts)
            else:
                yield self.handler_expried(ts - status_expried)
        except Exception as e:
            logging.error("handler ts error: %s %s", ts, e)
        finally:
            forsun_status.timeout_handling_count -= 1
            forsun_status.timeout_handled_count += 1

    @gen.coroutine
    def check(self, ts):
        try:
            if self.current_time is None:
                self.current_time = yield self.store.get_current()
                logging.info("start by last time %s current time %s", self.current_time, ts)

                @gen.coroutine
                def check_last(self, current_time, ts):
                    count = ts - current_time
                    while current_time < ts:
                        yield self.handler(current_time)
                        current_time += 1
                    logging.info("end by last time %s current time %s", current_time - count, ts)

                if self.current_time > 0:
                    self.ioloop.add_callback(check_last, self, self.current_time, ts)

            self.current_time = ts
            yield self.store.set_current(self.current_time)
            yield self.handler(ts)
        except Exception as e:
            logging.error("check error: %s %s", ts, e)

    def time_out(self, ts):
        if self.ioloop:
            self.ioloop.add_callback(self.check, ts)
            if self.current_time and self.current_time - ts >= 5:
                logging.warning("timeout handle delayed %s %s", ts, self.current_time)
        else:
            logging.warning("timeout empty %s", ts)

    @gen.coroutine
    def create_plan(self, plan):
        oplan = yield self.store.get_plan(plan.key)
        if oplan:
            yield self.store.remove_time_plan(oplan.next_time, oplan.key)
            yield self.store.remove_plan(oplan.key)
        if not plan.next_time:
            raise error.WillNeverArriveTimeError()

        try:
            action.get_driver(plan.action)
        except action.UnknownActionError:
            raise error.UnknownActionError()

        yield self.store.add_time_plan(plan.next_time, plan.key)
        res = yield self.store.set_plan(plan)
        forsun_status.plan_count += 1
        if not res:
            raise error.StorePlanError

    @gen.coroutine
    def remove_plan(self, key):
        oplan = yield self.store.get_plan(key)
        if not oplan:
            raise error.NotFoundPlanError()

        yield self.store.remove_time_plan(oplan.next_time, oplan.key)
        yield self.store.remove_plan(oplan.key)
        forsun_status.plan_count -= 1
        raise gen.Return(oplan)

    @gen.coroutine
    def get_pan(self, key):
        plan = yield self.store.get_plan(key)
        if not plan:
            raise error.NotFoundPlanError()

        status = yield self.store.get_time_plan(plan.last_timeout, key)
        plan.status = status
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
        keys = yield self.store.get_time_plans(ts)
        plans = []
        for key in keys:
            plan = yield self.store.get_plan(key)
            if plan:
                status = yield self.store.get_time_plan(plan.last_timeout, plan.key)
                plan.status = status

                plans.append(plan)
        raise gen.Return(plans)

    def serve(self, callback = None):
        try:
            def init():
                self.ioloop = IOLoop.current()
                self.ioloop.add_callback(self.init)
                self.ioloop.add_callback(logging.info, "forsun ready %s", os.getpid())
                self.read_event.set()

                if callback and callable(callback):
                    self.ioloop.add_callback(lambda : callback(self))

            self.server.start(init)
            self.read_event.wait()
            if config.get("SERVER_MODE", "").upper() in ("", "TIMER"):
                timer.start(self.time_out, self.exit)
            else:
                timer.start(lambda ts: None, self.exit)
            timer.loop()
        except KeyboardInterrupt:
            self.exit()

    def exit(self, callback = None):
        @gen.coroutine
        def on_exit():
            yield self.uninit()
            self.server.stop()
            timer.stop()

            if callback and callable(callback):
                callback(self)
            logging.info("stoped current time %s", timer.current())

        logging.info("stoping current time %s", timer.current())
        if self.ioloop is None:
            self.read_event.set()
            timer.stop()
        else:
            self.ioloop.add_callback(on_exit)
        logging.info("stoping")
