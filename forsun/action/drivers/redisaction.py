# -*- coding: utf-8 -*-
# 15/7/3
# create by: snower

import time
import logging
from tornado.ioloop import IOLoop
from tornado import gen
from tornado.concurrent import Future
import tornadis
from ..action import Action, ExecuteActionError
from ...utils import parse_cmd
from ... import config
from ...error import ActionExecuteRetry

class RedisClient(object):
    def __init__(self, host, port, selected_db = 0, password = None, max_connections = 4, client_timeout = 7200, bulk_size = 5):
        self.ioloop = IOLoop.current()
        self.max_connections = max_connections
        self.current_connections = 0
        self.bulk_size = bulk_size
        self.pool = tornadis.ClientPool(
            max_size = -1,
            client_timeout = client_timeout,
            autoclose = True,
            host= host,
            port = port,
            db = selected_db,
            password = password,
            tcp_nodelay = True,
        )
        self._commands = []
        self.executing = False

    @gen.coroutine
    def execute(self):
        self.current_connections += 1
        try:
            connect_error_count = 0
            while self._commands:
                with (yield self.pool.connected_client()) as client:
                    if isinstance(client, Exception):
                        if self.current_connections != 1:
                            break

                        logging.error("redis store connect error: %s", client)
                        connect_error_count += 1
                        if connect_error_count <= 2:
                            yield gen.sleep(2)
                        else:
                            commands, self._commands = self._commands, []
                            for command in commands:
                                command[2].set_exception(client)
                        continue

                    if self._commands:
                        commands, self._commands = self._commands[:self.bulk_size], self._commands[self.bulk_size:]
                        if len(self._commands) > self.bulk_size and self.current_connections < self.max_connections:
                            self.ioloop.add_callback(self.execute)

                        try:
                            if len(commands) == 1:
                                reply = yield client.call(*commands[0][0], **commands[0][1])
                                if isinstance(reply, Exception):
                                    commands[0][2].set_exception(reply)
                                else:
                                    commands[0][2].set_result(reply)
                            else:
                                pipeline = tornadis.Pipeline()
                                for command in commands:
                                    pipeline.stack_call(*command[0])
                                replys = yield client.call(pipeline)
                                if isinstance(replys, Exception):
                                    for command in commands:
                                        command[2].set_exception(replys)
                                else:
                                    if isinstance(replys, (list, tuple)):
                                        for i in range(len(replys)):
                                            if isinstance(replys[i], Exception):
                                                commands[i][2].set_exception(replys[i])
                                            else:
                                                commands[i][2].set_result(replys[i])
                                    else:
                                        for command in commands:
                                            command[2].set_result(replys)
                        except Exception as e:
                            for command in commands:
                                if not command[2].done():
                                    command[2].set_exception(e)
        finally:
            self.current_connections -= 1
            if self.current_connections == 0:
                self.executing = False

    def execute_command(self, *args, **kwargs):
        future = Future()
        self._commands.append((args, kwargs, future))
        if not self.executing:
            self.ioloop.add_callback(self.execute)
            self.executing = True
        return future

class RedisAction(Action):
    client_pools = {}

    def __init__(self, *args, **kwargs):
        super(RedisAction, self).__init__(*args, **kwargs)

        self.start_time  = time.time()

    def get_client(self, host, port, selected_db, password, max_connections):
        key = "%s:%s:%s" % (host, port, selected_db)
        if key not in self.client_pools:
            client_timeout = int(config.get("ACTION_REDIS_CLIENT_TIMEOUT", 8))
            bulk_size = int(config.get("ACTION_REDIS_BULK_SIZE", 8))
            self.__class__.client_pools[key] = RedisClient(host = host, port = port, selected_db = selected_db, max_connections = max_connections,
                                                           client_timeout = client_timeout, bulk_size = bulk_size)
        return self.__class__.client_pools[key]

    @gen.coroutine
    def execute(self, *args, **kwargs):
        if len(self.params) < 2:
            raise ExecuteActionError("redis params is empty")

        host = self.params.get("host", "127.0.0.1")
        port = int(self.params.get("port", 6379))
        selected_db = int(self.params.get("selected_db", 0))
        password = self.params.get("password", None)
        max_connections = int(self.params.get("max_connections", config.get("ACTION_REDIS_MAX_CONNECTIONS", 8)))
        command = self.params.get("command")
        cmds = parse_cmd(command, True)

        if cmds:
            try:
                client = self.get_client(host, port, selected_db, password, max_connections)
                try:
                    futures = []
                    for cmd, args in cmds:
                        future = client.execute_command(cmd, *args)
                        futures.append(future)
                    yield futures
                except Exception as e:
                    logging.debug("redis action execute '%s' %s:%s/%s '%s' %s %.2fms", self.plan.key, host, port,
                                  selected_db, cmds, e, (time.time() - self.start_time) * 1000)
            except Exception as e:
                logging.debug("redis action execute '%s' %s:%s/%s '%s' %s %.2fms", self.plan.key, host, port,
                              selected_db, cmds, e, (time.time() - self.start_time) * 1000)
                raise ActionExecuteRetry()
        logging.debug("redis action execute '%s' %s:%s/%s '%s' %.2fms", self.plan.key, host, port, selected_db,
                      cmds, (time.time() - self.start_time) * 1000)