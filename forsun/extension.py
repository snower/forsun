# -*- coding: utf-8 -*-
# 18/1/26
# create by: snower

import logging
from .store import Store, register_store
from .action import Action, register_action

class ExtensionManager(type):
    extensions = []

    @classmethod
    def add_extension(cls, extension):
        cls.extensions.append(extension)

    @classmethod
    def get_extensions(cls):
        return cls.extensions

    @classmethod
    def register(cls):
        for extension_cls in cls.extensions:
            try:
                setattr(extension_cls, "_instance", extension_cls())
                extension_cls._instance.register()
            except Exception as e:
                logging.error("extension register error: %s %s %s", extension_cls, extension_cls.name, e)

    @classmethod
    def init(cls):
        for extension_cls in cls.extensions:
            if hasattr(extension_cls, "_instance") and extension_cls._instance:
                try:
                    extension_cls._instance.init()
                except Exception as e:
                    logging.error("extension init error: %s %s %s", extension_cls, extension_cls.name, e)

    @classmethod
    def uninit(cls):
        for extension_cls in cls.extensions:
            if hasattr(extension_cls, "_instance") and extension_cls._instance:
                try:
                    extension_cls._instance.uninit()
                    extension_cls._instance = None
                except Exception as e:
                    logging.error("extension uninit error: %s %s %s", extension_cls, extension_cls.name, e)

class Extension(object):
    name = ""

    def register_store(self, name, cls):
        return register_store(name, cls)

    def register_action(self, name, cls):
        return register_action(name, cls)

    def register(self):
        pass

    def init(self):
        pass

    def uninit(self):
        pass