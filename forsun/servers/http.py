# -*- coding: utf-8 -*-
# 18/3/14
# create by: snower

import time
import json
from tornado import gen
from tornado.web import RequestHandler as BaseRequestHandler
from tornado.web import HTTPError
from tornado.httpserver import HTTPServer as BaseHTTPServer
from tornado.web import Application as BaseApplication
from ..plan import Plan
from ..utils import parse_cmd, unicode_type
from ..status import forsun_status
from ..error import ForsunPlanError, RequiredArgumentError, NotFoundPlanError

def execute(func):
    @gen.coroutine
    def _(self, *args, **kwargs):
        forsun_status.http_requesting_count += 1
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
            forsun_status.http_requested_error_count += 1
            data = {
                "errcode": 1001,
                "errmsg": u"未知错误",
                "data": {}
            }
        finally:
            forsun_status.http_requested_count += 1
            forsun_status.http_requesting_count -= 1
        self.finish(data)
    return _

class RequestHandler(BaseRequestHandler):
    is_timeout = False

    def prepare(self):
        if self.request.method.lower() in ("post", "put"):
            content_type = self.request.headers.get("Content-Type", "application/json")
            if content_type.startswith("application/json"):
                try:
                    if not isinstance(self.request.body, unicode_type):
                        body = unicode_type(self.request.body, "utf-8")
                    else:
                        body = self.request.body
                    self.request.body_arguments = json.loads(body)
                    if isinstance(self.request.body_arguments, dict):
                        if self.request.method.lower() == "put":
                            self.request.body_arguments["method"] = "createTimeout"
                        else:
                            self.request.body_arguments["method"] = "create"
                        self.request.body_arguments = [self.request.body_arguments]
                except:
                    raise HTTPError(400, u"请求数据类型application/json解析失败")
            elif content_type.startswith("application/crontab"):
                try:
                    if not isinstance(self.request.body, unicode_type):
                        body = unicode_type(self.request.body, "utf-8")
                    else:
                        body = self.request.body
                    self.request.body_arguments = self.parse_cmd(body)
                except:
                    import traceback
                    traceback.print_exc()
                    raise HTTPError(400, u"请求数据类型接受application/crontab解析失败")
            else:
                raise HTTPError(400, u"未知数据类型")


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

    def parse_cmd(self, body):
        arguments = []
        for b in body.split("\n"):
            cmds = parse_cmd(b, True, False)
            for cmd in cmds:
                key, seconds, minutes, hours, days, months, weeks, action, params_str = cmd

                is_timeout = False
                for ct in [seconds, minutes, hours, days, months, weeks]:
                    if ct.startswith("*/"):
                        is_timeout = True
                        break

                params = {}
                for cmd, args in parse_cmd(params_str):
                    if isinstance(cmd, tuple):
                        params[cmd[0]] = cmd[1]
                    else:
                        params[cmd] = args

                if is_timeout:
                    def parse_time(ct, count):
                        if not ct.startswith("*/"):
                            return 0, count

                        ct = ct.split("/")
                        return (int(ct[1]), int(ct[2])) if len(ct) >= 3 else (int(ct[1]), count)

                    count = 1
                    seconds, count = parse_time(seconds, count)
                    minutes, count = parse_time(minutes, count)
                    hours, count = parse_time(hours, count)
                    days, count = parse_time(days, count)
                    months, count = parse_time(months, count)
                    weeks, count = parse_time(weeks, count)
                else:
                    count = 0
                    seconds = int(seconds) if seconds != "*" else -1
                    minutes = int(minutes) if minutes != "*" else -1
                    hours = int(hours) if hours != "*" else -1
                    days = int(days) if days != "*" else -1
                    months = int(months) if months != "*" else -1
                    weeks = int(weeks) if weeks != "*" else -1

                arguments.append({
                    "method": "createTimeout" if is_timeout else "create",
                    "key": key,
                    "seconds": seconds,
                    "minute": minutes,
                    "hour": hours,
                    "day": days,
                    "month": months,
                    "week": weeks,
                    "count": count,
                    "action": action,
                    "params": params,
                })
        return arguments

    @gen.coroutine
    def create_plan(self):
        plans = []
        for arguments in self.request.body_arguments:
            key = arguments.get("key", "")
            seconds = int(arguments.get("seconds", -1))
            minute = int(arguments.get("minute", -1))
            hour = int(arguments.get("hour", -1))
            day = int(arguments.get("day", -1))
            month = int(arguments.get("month", -1))
            week = int(arguments.get("week", -1))
            count = int(arguments.get("count", 0))
            action = arguments.get("action", "shell")
            params = arguments.get("params", {})
            if not isinstance(params, dict):
                continue

            if arguments.get("method", "createTimeout") == "createTimeout":
                plan = Plan(key, seconds, minute, hour, day, month, week, is_time_out=True, count=count, action=action, params=params,
                            created_time=time.mktime(time.gmtime()))
                yield self.application.forsun.create_plan(plan)
            else:
                plan = Plan(key, seconds, minute, hour, day, month, week, is_time_out=False, action=action, params=params,
                        created_time=time.mktime(time.gmtime()))
                yield self.application.forsun.create_plan(plan)
            plans.append(self.plan_to_dict(plan))
        if not plans:
            raise RequiredArgumentError()
        raise gen.Return(plans[0] if len(plans) == 1 else plans)

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
        plan = yield self.create_plan()
        raise gen.Return(plan)

    @execute
    @gen.coroutine
    def put(self):
        plan = yield self.create_plan()
        raise gen.Return(plan)

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

class InfoRequestHandler(RequestHandler):
    @execute
    @gen.coroutine
    def get(self):
        info =  forsun_status.get_info()
        raise gen.Return(info)

class HTTPServer(BaseHTTPServer):
    def handle_stream(self, *args, **kwargs):
        r = super(HTTPServer, self).handle_stream(*args, **kwargs)
        forsun_status.http_connecting_count+=1
        forsun_status.http_connected_count += 1
        return r

    def on_close(self, *args, **kwargs):
        r = super(HTTPServer, self).on_close(*args, **kwargs)
        forsun_status.http_connecting_count -= 1
        return r

class Application(BaseApplication):
    def __init__(self, forsun, *args, **kwargs):
        self.forsun = forsun

        urls = (
            (r'^/v1/ping$', PingRequestHandler),
            (r'^/v1/plan$', PlanRequestHandler),
            (r'^/v1/time$', TimeRequestHandler),
            (r'^/v1/keys$', KeysRequestHandler),
            (r'^/v1/info$', InfoRequestHandler),
        )

        super(Application, self).__init__(urls, *args, **kwargs)