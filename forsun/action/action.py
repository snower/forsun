# -*- coding: utf-8 -*-
# 15/6/27
# create by: snower

from tornado import gen

class Action(object):
    @gen.coroutine
    def execute(self, *args, **kwargs):
        raise NotImplementedError()