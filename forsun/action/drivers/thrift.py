# -*- coding: utf-8 -*-
# 15/7/3
# create by: snower

import time
import json
import logging
from tornado import gen
from ...utils import load_extensions
from ...clients.thrift import TorThriftClient
from ..action import Action, ExecuteActionError

class ThriftAction(Action):
    client_pools = {}

    def __init__(self, *args, **kwargs):
        super(ThriftAction, self).__init__(*args, **kwargs)

        self.start_time  = time.time()

    @gen.coroutine
    def init(cls):
        pass

    def get_client(self, host, port, pool, max_connections, client_cls):
        from torthrift.transport import TStreamPool, TStream
        from torthrift.transport import TIOStreamTransportPool, TIOStreamTransport
        from torthrift.protocol import TBinaryProtocolPool, TBinaryProtocol
        from torthrift.client import PoolClient

        if pool:
            pool = self.client_pools.get("%s:%s" % (host, port), None)
            if not pool:
                transport = TStreamPool(host, port, max_connections)
                transport = TIOStreamTransportPool(transport)
                pool = TBinaryProtocolPool(transport)
                self.client_pools["%s:%s" % (host, port)] = pool
            client = PoolClient(client_cls, pool)
            setattr(client, "close", lambda : None)
        else:
            transport = TStream(host, port)
            transport = TIOStreamTransport(transport)
            protocol = TBinaryProtocol(transport)
            client = client_cls(protocol)
            setattr(client, "close", lambda : transport.close())
        return client

    @gen.coroutine
    def execute(self, *args, **kwargs):
        if not self.params:
            raise ExecuteActionError("is empty")

        method = self.params[0]
        args = self.params[1] if len(self.params) >= 3 and self.params[1] else '[]'
        if args:
            try:
                args = tuple(json.loads(args))
            except:
                args = tuple()

        options = self.params[-1] if self.params[-1] else "{}"
        if options:
            try:
                options = json.loads(options)
            except:
                options = {}
        host = options.get("host", "127.0.0.1")
        port = int(options.get("port", 5643))
        pool = bool(options.get("pool", False))
        max_connections = int(options.get("max_connections", 1))


        if method.startswith("forsun"):
            method = method.split(".")[-1]
            client_cls = TorThriftClient
        else:
            module = "".join(method.split(".")[:-1])
            client_cls = load_extensions(module)
            method = method.split(".")[-1]
        client = self.get_client(host, port, pool, max_connections, client_cls)
        yield getattr(client, method)(*args)
        client.close()
        logging.info("redis action %s:%s %s %s %.2fms", host, port, self.params[0], args, (time.time() - self.start_time) * 1000)