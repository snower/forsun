# -*- coding: utf-8 -*-
# 15/6/8
# create by: snower

import sys
import time
from tornado.concurrent import TracebackFuture
from tornado import gen
import tornadoredis
from ... import config
from ...plan import Plan
from ..store import Store

class RedisClient(object):
    def __init__(self, *args, **kwargs):
        self.db = tornadoredis.Client(*args, **kwargs)

    def __getattr__(self, name):
        method = getattr(self.db, name)
        def _(*args, **kwargs):
            future = TracebackFuture()
            def finish(res):
                future.set_result(res)
            try:
                kwargs["callback"] = finish
                method(*args, **kwargs)
            except:
                future.set_exc_info(sys.exc_info())
            return future
        setattr(self, name, _)
        return _

class RedisStore(Store):
    def __init__(self, *args, **kwargs):
        super(RedisClient, self).__init__(*args, **kwargs)

        self.db = RedisClient(
            host = config.get("STORE_REDIS_HOST", "127.0.0.1"),
            port = config.get("STORE_REDIS_PORT", 6379),
            selected_db = config.get("STORE_REDIS_HOST", 1),
        )
        self.prefix = config.get("STORE_REDIS_PREFIX", "forsun")
        if config.get("STORE_REDIS_SERVER_ID"):
            self.prefix += ":" + config.get("STORE_REDIS_SERVER_ID")

    def get_key(self, key):
        return "%s:%s" % (self.prefix, key)

    @gen.coroutine
    def store_plan(self, plan):
        key = plan.key
        yield self.db.sadd(self.get_key("keys"), key)
        res = yield self.db.set(self.get_key("key:%s" % key), plan.dupms(), expire = int(plan.next_time - time.time() + 30))
        raise gen.Return(res)

    @gen.coroutine
    def has_key(self, key):
        res = yield self.db.sismember(self.get_key("keys"), key)
        raise gen.Return(res)

    @gen.coroutine
    def load_plan(self, key):
        res = yield self.db.get(self.get_key("key:%s" % key))
        if res:
            res = Plan.loads(res)
        raise gen.Return(res)

    @gen.coroutine
    def remove_plan(self, key):
        res = yield self.db.delete(self.get_key("key:%s" % key))
        yield self.db.srem(self.get_key("keys"), key)
        raise gen.Return(res)

    @gen.coroutine
    def add_time_plan(self, plan):
        res = yield self.db.hset(self.get_key("time:%s" % plan.next_time), plan.key, plan.dupms())
        yield self.db.expire(self.get_key("time:%s" % plan.next_time), int(plan.next_time - time.time() + 30))
        raise gen.Return(res)

    @gen.coroutine
    def get_time_plan(self, ts):
        res = yield self.db.hgetall(self.get_key("time:%s" % ts))
        res = res or {}
        results = {}
        for key, plan in res.iteritems():
            results[key] = Plan.loads(plan)
        raise gen.Return(results)

    @gen.coroutine
    def remove_time_plan(self, plan):
        res = yield self.db.hdel(self.get_key("time:%s" % plan.next_time), plan.key)
        raise gen.Return(res)