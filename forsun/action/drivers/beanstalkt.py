# -*- coding: utf-8 -*-
# 15/7/3
# create by: snower

import time
from tornado import gen
from ..action import Action

class BeanstalkAction(Action):
    client_pools = {}

    def __init__(self, *args, **kwargs):
        super(BeanstalkAction, self).__init__(*args, **kwargs)

        self.start_time  = time.time()

    @classmethod
    def init(cls):
        pass

    @gen.coroutine
    def execute(self, *args, **kwargs):
        pass