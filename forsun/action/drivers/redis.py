# -*- coding: utf-8 -*-
# 15/7/3
# create by: snower

import time
import json
import logging
from tornado import gen
import tornadoredis
from ..action import Action, ExecuteActionError

class RedisAction(Action):
    client_pools = {}

    def __init__(self, *args, **kwargs):
        super(RedisAction, self).__init__(*args, **kwargs)

        self.start_time  = time.time()

    @classmethod
    def init(cls):
        pass

    def get_client(self, host, port, selected_db, pool, max_connections):
        if pool:
            pool = self.client_pools.get("%s:%s" % (host, port), None)
            if not pool:
                pool = tornadoredis.ConnectionPool(max_connections = max_connections, wait_for_available = True,
                                                   host = host, port = port)
                self.client_pools["%s:%s" % (host, port)] = pool
            client = tornadoredis.Client(selected_db= selected_db, connection_pool= pool)
        else:
            client = tornadoredis.Client(host= host, port= port, selected_db= selected_db)
        return client

    @gen.coroutine
    def execute(self, *args, **kwargs):
        if len(self.params) < 2:
            raise ExecuteActionError("redis params is empty")

        options = self.params[-1] if self.params[-1] else "{}"
        if options:
            try:
                options = json.loads(options)
            except:
                options = {}

        host = options.get("host", "127.0.0.1")
        port = int(options.get("port", 6379))
        selected_db = int(options.get("selected_db", 0))
        pool = bool(options.get("pool", False))
        max_connections = int(options.get("max_connections", 1))

        client = self.get_client(host, port, selected_db, pool, max_connections)
        cmd = self.params[0].upper()
        args = tuple(self.params[1:-1])
        yield gen.Task(client.execute_command, cmd, *args)
        yield gen.Task(client.disconnect)
        logging.info("redis action %s:%s/%s %s %s %.2fms", host, port, selected_db, cmd, args, (time.time() - self.start_time) * 1000)