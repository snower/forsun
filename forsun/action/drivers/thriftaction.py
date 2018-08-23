# -*- coding: utf-8 -*-
# 15/7/3
# create by: snower

import time
import logging
from tornado import gen
from thrift.protocol.TBinaryProtocol import TBinaryProtocolFactory
from thrift.Thrift import TApplicationException
from torthrift.pool import TStreamPool
from torthrift.client import PoolClient
from ...clients.client.Forsun import Client
from ..action import Action, ExecuteActionError
from ... import config
from ...error import ActionExecuteRetry

class ThriftAction(Action):
    client_pools = {}

    def __init__(self, *args, **kwargs):
        super(ThriftAction, self).__init__(*args, **kwargs)

        self.start_time  = time.time()

    def get_client(self, host, port, max_connections = 0):
        key = "%s:%s" % (host, port)
        if key not in self.client_pools:
            self.__class__.client_pools[key] = PoolClient(Client, TStreamPool(host, port, max_stream=max_connections), TBinaryProtocolFactory())
        elif max_connections:
            self.client_pools[key]._itrans_pool._max_stream = max_connections
        return self.client_pools[key]

    @gen.coroutine
    def execute(self, *args, **kwargs):
        if not self.params:
            raise ExecuteActionError("is empty")

        host = self.params.get("host", "127.0.0.1")
        port = int(self.params.get("port", 5643))
        max_connections = int(self.params.get("max_connections", config.get("ACTION_THRIFT_MAX_CONNECTIONS", 64)))

        try:
            client = self.get_client(host, port, max_connections)
            try:
                yield client.forsun_call(self.plan.key, int(self.ts), self.params)
            except TApplicationException as e:
                logging.error("thrift action execute error '%s' %s:%s '%s' %.2fms", self.plan.key, host, port, e,
                              (time.time() - self.start_time) * 1000)
            else:
                logging.debug("thrift action execute '%s' %s:%s %.2fms", self.plan.key, host, port,
                              (time.time() - self.start_time) * 1000)
        except Exception as e:
            logging.error("thrift action execute error '%s' %s:%s '%s' %.2fms", self.plan.key, host, port, e,
                          (time.time() - self.start_time) * 1000)
            raise ActionExecuteRetry()