# -*- coding: utf-8 -*-
# 15/6/27
# create by: snower

from tornado import gen

class ExecuteActionError(Exception):
    pass

class Action(object):
    def __init__(self, ts, plan, action, params):
        self.ts = ts
        self.plan = plan
        self.action = action
        self.params = params

    @gen.coroutine
    def execute(self, *args, **kwargs):
        raise NotImplementedError()