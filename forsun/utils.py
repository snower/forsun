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

def parse_cmd(command, parse_kwargs = True):
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
        cmds.append((args[0], tuple(args[1:])))
    return cmds