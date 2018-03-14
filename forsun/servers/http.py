# -*- coding: utf-8 -*-
# 18/3/14
# create by: snower

import time
import json
from tornado import gen
from tornado.web import RequestHandler as BaseRequestHandler
from tornado.web import HTTPError
from tornado.web import Application as BaseApplication
from ..plan import Plan
from ..error import ForsunPlanError, RequiredArgumentError, NotFoundPlanError

def execute(func):
    @gen.coroutine
    def _(self, *args, **kwargs):
        try:
            result = yield func(self, *args, **kwargs)
            data = {
                "errcode": 0,
                "errmsg": "",
                "data": result
            }
        except ForsunPlanError as e:
            data = {
                "errcode": e.code,
                "errmsg": e.message,
                "data": {}
            }
        except Exception as e:
            data = {
                "errcode": 1001,
                "errmsg": u"未知错误",
                "data": {}
            }
        self.finish(data)
    return _

class RequestHandler(BaseRequestHandler):
    def prepare(self):
        if self.request.method.lower() in ("post", "put"):
            try:
                self.request.body_arguments = json.loads(self.request.body)
                self.request.arguments.update(self.request.body_arguments)
            except:
                raise HTTPError(400, u"请求数据类型接受application/json")

    def plan_to_dict(self, plan):
        return {
            "key": plan.key,
            "second": plan.second,
            "minute": plan.minute,
            "hour": plan.hour,
            "day": plan.day,
            "month": plan.month,
            "week": plan.week,
            "status": plan.status,
            "count": plan.count,
            "is_time_out": plan.is_time_out,
            "next_time": plan.next_time,
            "current_count": plan.current_count,
            "last_timeout": plan.last_timeout,
            "created_time": plan.created_time,
            "action": plan.action,
            "params": plan.params,
        }

class PingRequestHandler(RequestHandler):
    @execute
    @gen.coroutine
    def get(self):
        raise gen.Return({})

class PlanRequestHandler(RequestHandler):
    @execute
    @gen.coroutine
    def get(self):
        key = self.get_query_argument("key")
        if not key:
            raise RequiredArgumentError("key")

        plan = yield self.application.forsun.get_pan(key)
        if not plan:
            raise NotFoundPlanError()
        raise gen.Return(self.plan_to_dict(plan))

    @execute
    @gen.coroutine
    def post(self):
        key = self.request.body_arguments.get("key", "")
        second = int(self.request.body_arguments.get("second", -1))
        minute = int(self.request.body_arguments.get("minute", -1))
        hour = int(self.request.body_arguments.get("hour", -1))
        day = int(self.request.body_arguments.get("day", -1))
        month = int(self.request.body_arguments.get("month", -1))
        week = int(self.request.body_arguments.get("week", -1))
        action = self.request.body_arguments.get("action", "shell")
        params = self.request.body_arguments.get("params", {})
        if not isinstance(params, dict):
            raise RequiredArgumentError("params")

        plan = Plan(key, second, minute, hour, day, month, week, is_time_out=False, action=action, params=params,
                    created_time=time.mktime(time.gmtime()))
        yield self.application.forsun.create_plan(plan)
        raise gen.Return(self.plan_to_dict(plan))

    @execute
    @gen.coroutine
    def put(self):
        key = self.request.body_arguments.get("key", "")
        second = int(self.request.body_arguments.get("second", 1))
        minute = int(self.request.body_arguments.get("minute", -1))
        hour = int(self.request.body_arguments.get("hour", -1))
        day = int(self.request.body_arguments.get("day", -1))
        month = int(self.request.body_arguments.get("month", -1))
        week = int(self.request.body_arguments.get("week", -1))
        count = int(self.request.body_arguments.get("count", 0))
        action = self.request.body_arguments.get("action", "shell")
        params = self.request.body_arguments.get("params", {})
        if not isinstance(params, dict):
            raise RequiredArgumentError("params")

        plan = Plan(key, second, minute, hour, day, month, week, is_time_out=True, count = count, action=action, params=params,
                    created_time=time.mktime(time.gmtime()))
        yield self.application.forsun.create_plan(plan)
        raise gen.Return(self.plan_to_dict(plan))

    @execute
    @gen.coroutine
    def delete(self):
        key = self.get_query_argument("key")
        if not key:
            raise RequiredArgumentError("key")

        plan = yield self.application.forsun.remove_plan(key)
        if not plan:
            raise NotFoundPlanError()
        raise gen.Return(self.plan_to_dict(plan))

class TimeRequestHandler(RequestHandler):
    @execute
    @gen.coroutine
    def get(self):
        timestamp = self.get_query_argument("timestamp", default=0)

        current_timestamp = yield self.application.forsun.get_current_time()
        if not timestamp:
            timestamp = current_timestamp
        else:
            try:
                timestamp = int(timestamp)
            except:
                raise RequiredArgumentError("timestamp")

        plans = yield self.application.forsun.get_time_plans(timestamp)
        raise gen.Return({
            "plans": [self.plan_to_dict(plan) for plan in plans],
            "current_timestamp": current_timestamp,
        })

class KeysRequestHandler(RequestHandler):
    @execute
    @gen.coroutine
    def get(self):
        prefix = self.get_query_argument("prefix", default="")

        keys = yield self.application.forsun.get_keys(prefix)
        raise gen.Return(keys)

class Application(BaseApplication):
    def __init__(self, forsun, *args, **kwargs):
        self.forsun = forsun

        urls = (
            (r'^/v1/ping$', PingRequestHandler),
            (r'^/v1/plan$', PlanRequestHandler),
            (r'^/v1/time$', TimeRequestHandler),
            (r'^/v1/keys$', KeysRequestHandler),
        )

        super(Application, self).__init__(urls, *args, **kwargs)