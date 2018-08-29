# -*- coding: utf-8 -*-
# 15/7/2
# create by: snower

from tornado import gen
from thrift.transport.TSocket import TSocket
from thrift.transport.TTransport import TBufferedTransport
from thrift.protocol.TBinaryProtocol import TBinaryProtocol, TBinaryProtocolFactory
from torthrift.pool import TStreamPool
from torthrift.client import PoolClient
from .client.Forsun import Client
from .client.Forsun import ForsunPlanError

class ThriftClient(object):
    def __init__(self, port=6458, host="127.0.0.1"):
        self.host = host
        self.port = port
        self.client = None
        self.transport = None

    def connect(self):
        self.transport = TSocket(self.host, self.port)
        self.transport = TBufferedTransport(self.transport)
        protocol = TBinaryProtocol(self.transport)
        self.client = Client(protocol)
        self.transport.open()

    def execute(self, name, *args, **kwargs):
        if self.client is None:
            self.connect()
        result = getattr(self.client, name)(*args, **kwargs)
        return result

    def create(self, key, second, minute = -1, hour = -1, day = -1, month = -1, week = -1, action="shell", params={}):
        return self.execute("create", key, second, minute, hour, day, month, week, action, params)

    def create_timeout(self, key, second, minute = -1, hour = -1, day = -1, month = -1, week = -1, count=1, action="shell", params={}):
        return self.execute("createTimeout", key, second, minute, hour, day, month, week, count, action, params)

    def remove(self, key):
        return self.execute("remove", key)

    def get(self, key):
        return self.execute("get", key)

    def get_current(self):
        return self.execute("getCurrent")

    def get_time(self, timestamp):
        return self.execute("getTime", timestamp)

    def get_keys(self, prefix=''):
        return self.execute("getKeys", prefix)

    def info(self):
        return self.execute("info")

    def __del__(self):
        if self.client:
            self.transport.close()
            self.transport = None
            self.client = None

class TorThriftClient(object):
    def __init__(self, port=6458, host="127.0.0.1", max_stream=4):
        self.host = host
        self.port = port
        self.max_stream = max_stream

        self.pool = self.init_pool()

    def init_pool(self):
        return PoolClient(Client, TStreamPool(self.host, self.port, max_stream=self.max_stream), TBinaryProtocolFactory())

    @gen.coroutine
    def create(self, key, second, minute = -1, hour = -1, day = -1, month = -1, week = -1, action="shell", params={}):
        res = yield self.pool.create(key, second, minute, hour, day, month, week, action, params)
        raise gen.Return(res)

    @gen.coroutine
    def create_timeout(self, key, second, minute = -1, hour = -1, day = -1, month = -1, week = -1, count=1, action="shell", params={}):
        res = yield self.pool.createTimeout(key, second, minute, hour, day, month, week, count, action, params)
        raise gen.Return(res)

    @gen.coroutine
    def remove(self, key):
        res = yield self.pool.remove(key)
        raise gen.Return(res)

    @gen.coroutine
    def get(self, key):
        res = yield self.pool.get(key)
        raise gen.Return(res)

    @gen.coroutine
    def get_current(self):
        res = yield self.pool.getCurrent()
        raise gen.Return(res)

    @gen.coroutine
    def get_time(self, timestamp):
        res = yield self.pool.getTime(timestamp)
        raise gen.Return(res)

    @gen.coroutine
    def get_keys(self, prefix=''):
        res = yield self.pool.getKeys(prefix)
        raise gen.Return(res)

    @gen.coroutine
    def info(self):
        res = yield self.pool.info()
        raise gen.Return(res)