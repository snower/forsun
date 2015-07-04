# -*- coding: utf-8 -*-
# 15/7/4
# create by: snower

class ExtensionsNotFound(Exception): pass

def load_extensions(name):
    try:
        if "." in name:
            names = name.split(".")
            module = __import__(".".join(names[:-1]), {}, {}, [names[-1]])
            return getattr(module, names[-1])
        else:
            return __import__(name)
    except ImportError:
        return ExtensionsNotFound(name)