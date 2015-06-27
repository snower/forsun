# -*- coding: utf-8 -*-
# 15/6/27
# create by: snower

from tornado import gen

class Store(object):
    @gen.coroutine
    def store_plan(self, plan):
        raise NotImplementedError()

    @gen.coroutine
    def has_key(self, key):
        raise NotImplementedError()

    @gen.coroutine
    def load_plan(self, key):
        raise NotImplementedError()

    @gen.coroutine
    def remove_plan(self, key):
        raise NotImplementedError()

    @gen.coroutine
    def add_time_plan(self, plan):
        raise NotImplementedError()

    @gen.coroutine
    def get_time_plan(self, ts):
        raise NotImplementedError()

    @gen.coroutine
    def remove_time_plan(self, plan):
        raise NotImplementedError()