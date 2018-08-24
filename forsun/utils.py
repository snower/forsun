# -*- coding: utf-8 -*-
# 15/7/4
# create by: snower

import sys

if sys.version_info[0] >= 3:
    is_py3 = True
    string_type = (str, bytes)
    unicode_type = str
    bytes_type = bytes
    number_type = int

    def ensure_bytes(s):
        if isinstance(s, str):
            return s.encode("utf-8")
        return bytes(s)

    def ensure_unicode(s):
        if isinstance(s, bytes):
            return s.decode("utf-8")
        return str(s)
else:
    is_py3 = False
    string_type = (str, unicode)
    unicode_type = unicode
    bytes_type = str
    number_type = (int, long)

    def ensure_bytes(s):
        if isinstance(s, unicode):
            return s.encode("utf-8")
        return str(s)

    def ensure_unicode(s):
        if isinstance(s, unicode):
            return s
        if isinstance(s, str):
            return s.decode("utf-8")
        return str(s).decode("utf-8")

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

def parse_cmd(command, parse_kwargs = True, split_cmd = True):
    cmds = []
    args = []
    carg = []
    is_string = False
    is_kwargs = False
    lc = None

    for c in command:
        if c in ('"', "'"):
            if is_string is False:
                is_string = c
                lc = c
                continue
            elif carg:
                if is_string == c:
                    if lc != '\\':
                        if is_kwargs:
                            args.append((is_kwargs, "".join(carg)))
                            is_kwargs = False
                        else:
                            args.append("".join(carg))
                        carg = []
                        lc = c
                        is_string = False
                        continue
                    else:
                        carg.pop()

        elif c in ('\n', '\t', ' ', '\r'):
            if not carg:
                lc = c
                continue
            elif not is_string:
                if is_kwargs:
                    args.append((is_kwargs, "".join(carg)))
                    is_kwargs = False
                else:
                    args.append("".join(carg))
                carg = []
                lc = c
                continue
        elif c == ';':
            if not is_string:
                if carg:
                    if is_kwargs:
                        args.append((is_kwargs, "".join(carg)))
                        is_kwargs = False
                    else:
                        args.append("".join(carg))

                if args:
                    cmds.append((args[0], tuple(args[1:])))
                args = []
                carg = []
                is_string = False
                lc = None
                continue
        elif c == "=":
            if parse_kwargs and not is_string:
                if carg:
                    is_kwargs = "".join(carg)
                    carg = []
                    lc = c
                    continue

        carg.append(c)
        lc = c

    if carg:
        if is_kwargs:
            args.append((is_kwargs, "".join(carg)))
        else:
            args.append("".join(carg))

    if args:
        if split_cmd:
            cmds.append((args[0], tuple(args[1:])))
        else:
            cmds.append(args)
    return cmds