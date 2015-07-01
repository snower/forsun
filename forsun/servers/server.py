# -*- coding: utf-8 -*-
# 15/6/27
# create by: snower

class Server(object):
    def __init__(self, forsun):
        self.forsun = forsun

    def start(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()