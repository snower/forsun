# -*- coding: utf-8 -*-
# 15/6/27
# create by: snower

from tornado import gen

class Store(object):
    @gen.coroutine
    def init(self):
        pass

    @gen.coroutine
    def uninit(self):
        pass

    @gen.coroutine
    def set_current(self, current_time):
        raise NotImplemented

    @gen.coroutine
    def get_current(self):
        raise NotImplemented

    @gen.coroutine
    def set_plan(self, plan):
        raise NotImplementedError()

    @gen.coroutine
    def get_plan(self, plan):
        raise NotImplementedError()

    @gen.coroutine
    def remove_plan(self, key):
        raise NotImplementedError()

    @gen.coroutine
    def has_plan(self, key):
        plan = yield self.get_plan(key)
        raise gen.Return(plan)

    @gen.coroutine
    def add_time_plan(self, plan):
        raise NotImplementedError()

    @gen.coroutine
    def get_time_plan(self, ts):
        raise NotImplementedError()

    @gen.coroutine
    def remove_time_plan(self, plan):
        raise NotImplementedError()

    @gen.coroutine
    def delete_time_plan(self, ts):
        raise NotImplementedError()

    @gen.coroutine
    def get_plan_keys(self, prefix=""):
        raise NotImplementedError()