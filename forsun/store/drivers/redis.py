# -*- coding: utf-8 -*-
# 15/6/8
# create by: snower

import logging
from tornado import ioloop
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado import gen
from tornado.concurrent import Future
import tornadis
from ... import config
from ...plan import Plan
from ..store import Store
from ...utils import is_py3
from ... import timer

class HookPeriodicCallback(PeriodicCallback):
    def __init__(self, callback, callback_time, *args, **kwargs):
        super(HookPeriodicCallback, self).__init__(callback, callback_time)

ioloop.PeriodicCallback = HookPeriodicCallback

class RedisClient(object):
    def __init__(self, host, port, selected_db = 0, password= None, max_connections = 4, client_timeout = 7200, bulk_size = 5):
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
                        if connect_error_count <= 5:
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

    def select(self, db):
        return self.execute_command("SELECT", db)

    def get(self, key, **kwargs):
        return self.execute_command('GET', key, **kwargs)

    def set(self, key, value, expire=None, pexpire=None,
            only_if_not_exists=False, only_if_exists=False, **kwargs):
        args = []

        if expire is not None:
            args.extend(("EX", expire))
        if pexpire is not None:
            args.extend(("PX", pexpire))
        if only_if_not_exists:
            args.append("NX")
        if only_if_exists:
            args.append("XX")

        return self.execute_command('SET', key, value, *args, **kwargs)

    def keys(self, key, **kwargs):
        return self.execute_command('KEYS', key, **kwargs)

    def expire(self, key, ttl, **kwargs):
        return self.execute_command('EXPIRE', key, ttl, **kwargs)

    def delete(self, *keys, **kwargs):
        return self.execute_command('DEL', *keys, **kwargs)

    def hgetall(self, key, **kwargs):
        return self.execute_command('HGETALL', key, **kwargs)

    def hset(self, key, field, value, **kwargs):
        return self.execute_command('HSET', key, field, value, **kwargs)

    def hget(self, key, field, **kwargs):
        return self.execute_command('HGET', key, field, **kwargs)

    def hdel(self, key, *fields, **kwargs):
        return self.execute_command('HDEL', key, *fields, **kwargs)

class RedisStore(Store):
    def __init__(self, *args, **kwargs):
        super(RedisStore, self).__init__(*args, **kwargs)

        self.db = None
        self.prefix = "%s:%s" % (config.get("STORE_REDIS_PREFIX", "forsun"), config.get("STORE_REDIS_SERVER_ID", 0))

    @gen.coroutine
    def init(self):
        host = config.get("STORE_REDIS_HOST", "127.0.0.1")
        port = config.get("STORE_REDIS_PORT", 6379)
        selected_db = config.get("STORE_REDIS_DB", 0)
        password = config.get("STORE_REDIS_PASSWORD", None)

        self.db = RedisClient(
            host=host,
            port=port,
            selected_db=selected_db,
            password = password or None,
            max_connections=int(config.get("STORE_REDIS_MAX_CONNECTIONS", 8)),
            client_timeout=int(config.get("STORE_REDIS_CLIENT_TIMEOUT", 7200)),
            bulk_size=int(config.get("STORE_REDIS_BULK_SIZE", 5)),
        )
        logging.info("use redis store %s:%s/%s", host, port, selected_db)

    @gen.coroutine
    def set_current(self, current_time):
        res = yield self.db.set(self.prefix + ":current:time", str(current_time), expire = config.get("STORE_REDIS_CURRENTTIME_EXPRIED", 2592000))
        raise gen.Return(res)

    @gen.coroutine
    def get_current(self):
        res = yield self.db.get(self.prefix + ":current:time")
        raise gen.Return(int(res or 0))

    @gen.coroutine
    def set_plan(self, plan):
        res = yield self.db.set("".join([self.prefix, ":plan:", plan.key]), plan.dumps(), expire = plan.next_time - timer.current() + config.get("STORE_REDIS_PLAN_EXPRIED", 604800))
        raise gen.Return(res)

    @gen.coroutine
    def remove_plan(self, key):
        res = yield self.db.delete("".join([self.prefix, ":plan:", key]))
        raise gen.Return(res)

    @gen.coroutine
    def get_plan(self, key):
        res = yield self.db.get("".join([self.prefix, ":plan:", key]))
        if not res:
            raise gen.Return(None)
        try:
            res = Plan.loads(res)
        except Exception as e:
            logging.error("redis store load plan error: %s %s", key, e)
            res = None
        raise gen.Return(res)

    @gen.coroutine
    def add_time_plan(self, next_time, key):
        time_key = "".join([self.prefix, ":time:", str(next_time)])
        res = yield self.db.hset(time_key, key, '0')
        yield self.db.expire(time_key, next_time - timer.current() + config.get("STORE_REDIS_PLANTIME_EXPRIED", 604800))
        raise gen.Return(res)

    @gen.coroutine
    def get_time_plan(self, next_time, key):
        time_key = "".join([self.prefix, ":time:", str(next_time)])
        res = yield self.db.hget(time_key, key)
        try:
            status = int(res)
        except:
            status = 0
        raise gen.Return(status)

    @gen.coroutine
    def set_time_plan(self, next_time, key, status):
        time_key = "".join([self.prefix, ":time:", str(next_time)])
        res = yield self.db.hset(time_key, key, str(status))
        yield self.db.expire(time_key, next_time - timer.current() + config.get("STORE_REDIS_PLANTIME_EXPRIED", 604800))
        raise gen.Return(res)

    @gen.coroutine
    def remove_time_plan(self, next_time, key):
        res = yield self.db.hdel("".join([self.prefix, ":time:", str(next_time)]), key)
        raise gen.Return(res)

    @gen.coroutine
    def get_time_plans(self, ts):
        res = yield self.db.hgetall("".join([self.prefix, ":time:", str(ts)]))
        if not res:
            raise gen.Return([])
        if is_py3:
            raise gen.Return([str(res[i], "utf-8") for i in range(0, len(res), 2)])
        else:
            raise gen.Return([res[i] for i in range(0, len(res), 2)])

    @gen.coroutine
    def delete_time_plans(self, ts):
        res = yield self.db.delete("".join([self.prefix, ":time:", str(ts)]))
        raise gen.Return(res)

    @gen.coroutine
    def get_plan_keys(self, prefix = ""):
        prefix_len = len(self.prefix + ":plan:")
        res = yield self.db.keys("".join([self.prefix, ":plan:", prefix, "*"]))
        if is_py3:
            raise gen.Return([str(r, "utf-8")[prefix_len: ] for r in res])
        else:
            raise gen.Return([r[prefix_len: ] for r in res])