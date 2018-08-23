# -*- coding: utf-8 -*-
# 15/7/3
# create by: snower

import time
import logging
import socket
from tornado import gen
from tornado.iostream import IOStream
import beanstalkt
from ..action import Action
from ...utils import unicode_type
from ...error import ActionExecuteRetry

class BeanstalktClient(beanstalkt.Client):
    def _reconnect(self):
        pass

    @gen.coroutine
    def connect(self):
        """Connect to beanstalkd server."""
        if not self.closed():
            return
        self._talking = False
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        self._stream = IOStream(self._socket)
        self._stream.set_close_callback(self._reconnect)
        yield self._stream.connect((self.host, self.port))

class BeanstalkAction(Action):
    client_pools = {}

    def __init__(self, *args, **kwargs):
        super(BeanstalkAction, self).__init__(*args, **kwargs)

        self.start_time  = time.time()

    @gen.coroutine
    def get_client(self, host, port, watch_key):
        key = "%s:%s:%s" % (host, port, watch_key)
        if key in self.client_pools:
            if self.client_pools[key].closed():
                del self.client_pools[key]

        if key not in self.client_pools:
            client = BeanstalktClient(host, port)
            yield client.connect()
            yield client.use(watch_key)
            if watch_key != "default":
                yield client.watch(watch_key)
                yield client.ignore("default")
            self.__class__.client_pools[key] = client
        raise gen.Return(self.client_pools[key])

    @gen.coroutine
    def execute(self, *args, **kwargs):
        host = self.params.get("host", "127.0.0.1")
        port = int(self.params.get("port", 11300))
        name = self.params.get('name', 'default')
        body = self.params.get("body", '')

        if not body:
            logging.error("beanstalk action execute error %s body is empty", self.plan.key)
            raise gen.Return(None)

        try:
            client = yield self.get_client(host, port, name)
            yield client.put(body.encode("utf-8") if isinstance(body, unicode_type) else body, ttr = 7200)
        except Exception as e:
            logging.error("beanstalk action execute error '%s' %s:%s '%s' '%s' '%s' %.2fms", self.plan.key, host,
                          port, name, body, e, (time.time() - self.start_time) * 1000)
            raise ActionExecuteRetry()
        else:
            logging.debug("beanstalk action execute '%s' %s:%s '%s' '%s' %.2fms", self.plan.key, host, port, name, body,
                          (time.time() - self.start_time) * 1000)