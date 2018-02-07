# -*- coding: utf-8 -*-
# 15/7/3
# create by: snower

import time
import logging
from tornado import gen
import beanstalkt
from ..action import Action
from ...utils import unicode_type

class BeanstalkAction(Action):
    client_pools = {}

    def __init__(self, *args, **kwargs):
        super(BeanstalkAction, self).__init__(*args, **kwargs)

        self.start_time  = time.time()

    @gen.coroutine
    def get_client(self, host, port, watch_key):
        key = "%s:%s:%s" % (host, port, watch_key)
        if key not in self.client_pools:
            client = beanstalkt.Client(host, port)
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

        client = yield self.get_client(host, port, name)
        yield client.put(body.encode("utf-8") if isinstance(body, unicode_type) else body, ttr = 7200)
        logging.debug("beanstalk action execute %s:%s '%s' %.2fms", host, port, name, (time.time() - self.start_time) * 1000)