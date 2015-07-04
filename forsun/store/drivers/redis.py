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
    def __init__(self, host, port, selected_db=0, max_connections=4):
        self.selected_db = selected_db
        self.pool = tornadoredis.ConnectionPool(
            max_connections = max_connections,
            wait_for_available = True,
            host= host,
            port = port,
        )

    def __getattr__(self, name):
        @gen.coroutine
        def _(*args, **kwargs):
            db = tornadoredis.Client(connection_pool=self.pool, selected_db=self.selected_db)
            method = getattr(db, name)
            res = yield gen.Task(method, *args, **kwargs)
            yield gen.Task(db.disconnect)
            raise gen.Return(res)
        setattr(self, name, _)
        return _

class RedisStore(Store):
    def __init__(self, *args, **kwargs):
        super(RedisStore, self).__init__(*args, **kwargs)

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
    def add_plan(self, plan):
        res = yield self.db.set(self.get_key("key:%s" % plan.key), plan.dupms(), expire = int(plan.next_time - time.time() + 30))
        raise gen.Return(res)

    @gen.coroutine
    def remove_plan(self, key):
        res = yield self.db.delete(self.get_key("key:%s" % key))
        raise gen.Return(res)

    @gen.coroutine
    def has_plan(self, key):
        res = yield self.db.exists(self.get_key("key:%s" % key))
        raise gen.Return(bool(res))

    @gen.coroutine
    def store_plan(self, plan):
        res = yield self.db.set(self.get_key("key:%s" % plan.key), plan.dupms(), expire = int(plan.next_time - time.time() + 30))
        raise gen.Return(res)

    @gen.coroutine
    def load_plan(self, key):
        res = yield self.db.get(self.get_key("key:%s" % key))
        if not res:
            raise gen.Return(None)
        try:
            res = Plan.loads(res)
        except:
            res = None
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
            try:
                results[key] = Plan.loads(plan)
            except:pass
        raise gen.Return(results)

    @gen.coroutine
    def remove_time_plan(self, plan):
        res = yield self.db.hdel(self.get_key("time:%s" % plan.next_time), plan.key)
        raise gen.Return(res)

    @gen.coroutine
    def get_plan_keys(self, prefix=""):
        res = yield self.db.keys(self.get_key("key:*" % prefix))
        raise gen.Return(res)