# -*- coding: utf-8 -*-
# 15/6/27
# create by: snower

from __future__ import absolute_import, division, print_function, with_statement

import time
import datetime
import argparse
from thrift.transport.TTransport import TTransportException
from ..clients import ThriftClient, ForsunPlanError
from ..utils import parse_cmd

parser = argparse.ArgumentParser(description='High-performance timing scheduling service')
parser.add_argument('--host', dest='host', default="127.0.0.1", help='host (default: 127.0.0.1)')
parser.add_argument('--port', dest='port', default=6458, type=int, help='port (default: 6458)')
parser.add_argument('--exe', dest='execute', default='', type=str, help='execute cmd (default: )')
parser.add_argument('cmd', default='', type=str, nargs=argparse.OPTIONAL, help='execute cmd (default: )')

client = None

def cmd_help(*args):
    print("help - show help doc")
    print("exit - exit the cmd")

    print("ls - show prfix key plans (ls [prefix or *])")
    print("current - show current time plans (current)")
    print("time - show time plans (time [timestamp or datetime])")
    print("get - show plan info (get [key])")
    print("rm - remove plan (rm [key])")
    print("set - add crontab plan (set [key] [seconds] [minutes] [hours] [days] [months] [weeks] [cmd] [args])")

def cmd_exit(*args):
    exit(0)

def cmd_ls(prefix = None, *args):
    keys = client.get_keys(prefix or '')
    for key in keys:
        print(key)

def cmd_current(*args):
    plans = client.get_current()
    for plan in plans:
        print(plan)

def cmd_time(ts = None, *args):
    if not ts:
        ts = int(time.time())
    elif ts.isdigit():
        ts = int(ts)
    else:
        ts = time.mktime(datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").timetuple())
    plans = client.get_time(ts)
    for plan in plans:
        print(plan)

def cmd_get(key, *args):
    plan = client.get(key)
    print(plan)

def cmd_rm(key, *args):
    client.remove(key)
    print('success')

def cmd_set(key, seconds, minutes, hours, days, months, weeks, action, params_str, *args):
    is_timeout = False
    for ct in [seconds, minutes, hours, days, months, weeks]:
        if ct.startswith("*/"):
            is_timeout = True
            break

    params = {}
    for cmd, args in parse_cmd(params_str):
        if isinstance(cmd, tuple):
            params[cmd[0]] = cmd[1]
        else:
            params[cmd] = args

    if is_timeout:
        def parse_time(ct, count):
            if not ct.startswith("*/"):
                return 0, count

            ct = ct.split("/")
            return (int(ct[1]), int(ct[2])) if len(ct) >= 3 else (int(ct[1]), count)

        count = 1
        seconds, count = parse_time(seconds, count)
        minutes, count = parse_time(minutes, count)
        hours, count = parse_time(hours, count)
        days, count = parse_time(days, count)
        months, count = parse_time(months, count)
        weeks, count = parse_time(weeks, count)

        plan = client.create_timeout(key, seconds, minutes, hours, days, months, weeks or -1, count, action, params)
    else:
        seconds = int(seconds) if seconds == "*" else -1
        minutes = int(minutes) if minutes == "*" else -1
        hours = int(hours) if hours == "*" else -1
        days = int(days) if days == "*" else -1
        months = int(months) if months == "*" else -1
        weeks = int(weeks) if weeks == "*" else -1

        plan = client.create(key, seconds, minutes, hours, days, months, weeks, action, params)

    print(plan)

def main():
    global client

    args = parser.parse_args()
    client = ThriftClient(args.port, args.host)

    try:
        client.connect()
    except TTransportException as e:
        print('connect forsun server fail: ', e.message)
        exit(1)

    CMDS = {
        'help': cmd_help,
        'exit': cmd_exit,

        'ls': cmd_ls,
        'current': cmd_current,
        'time': cmd_time,
        'get': cmd_get,
        'rm': cmd_rm,
        'set': cmd_set,
    }

    if args.execute or args.cmd:
        cmds = parse_cmd(args.cmd or args.execute)
        for cmd, params in cmds:
            if cmd not in CMDS:
                print('Unknown cmd ', cmd)
                exit(1)
            else:
                try:
                    CMDS[cmd](*params)
                except KeyboardInterrupt:
                    exit(0)
                except Exception as e:
                    print('cmd error: ', e)
                    exit(1)
        exit(0)

    print('Welcome to the Forsun')
    print("Type 'help' for help")
    print('')

    while True:
        try:
            command = raw_input("forsun> ")
            cmd, params = parse_cmd(command)
            if cmd not in CMDS:
                print('Unknown cmd ', cmd)
            else:
                try:
                    CMDS[cmd](*params)
                    print('')
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print('cmd error: ', e)
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()