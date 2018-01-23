# -*- coding: utf-8 -*-
# 15/7/3
# create by: snower

import time
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

    def get_client(self, host, port, selected_db, max_connections):
        key = "%s:%s:%s" % (host, port, selected_db)
        if key not in self.client_pools:
            self.__class__.client_pools[key] = tornadoredis.ConnectionPool(host = host, port = port, max_connections = max_connections, wait_for_available = True)
        return tornadoredis.Client(selected_db= selected_db, connection_pool= self.client_pools[key])

    def parse_cmd(self, command):
        args = []
        carg = []
        is_string = False
        lc = None

        for c in command:
            if c in ('"', "'"):
                if is_string is False:
                    is_string = c
                    lc = c
                    continue
                elif carg:
                    if is_string == c:
                        if lc != '\\':
                            args.append("".join(carg))
                            carg = []
                            lc = c
                            is_string = False
                            continue
                        else:
                            carg.pop()

            elif c in ('\n', '\t', ' ', '\r'):
                if not carg:
                    lc = c
                    continue
                elif not is_string:
                    args.append("".join(carg))
                    carg = []
                    lc = c
                    continue

            carg.append(c)
            lc = c

        if carg:
            args.append("".join(carg))

        return args[0], tuple(args[1:])

    @gen.coroutine
    def execute(self, *args, **kwargs):
        if len(self.params) < 2:
            raise ExecuteActionError("redis params is empty")

        host = self.params.get("host", "127.0.0.1")
        port = int(self.params.get("port", 6379))
        selected_db = int(self.params.get("selected_db", 0))
        max_connections = int(self.params.get("max_connections", 1))
        command = self.params.get("command")
        cmd, args = self.parse_cmd(command)

        client = self.get_client(host, port, selected_db, max_connections)
        yield gen.Task(client.execute_command, cmd, *args)
        yield gen.Task(client.disconnect)
        logging.info("redis action execute %s:%s/%s %s %.2fms", host, port, selected_db, cmd, (time.time() - self.start_time) * 1000)