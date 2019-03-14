# -*- coding: utf-8 -*-
# 15/6/27
# create by: snower

from __future__ import absolute_import, division, print_function, with_statement

import time
import datetime
import argparse
import pytz
import tzlocal
from thrift.transport.TTransport import TTransportException
from ..version import version
from ..clients import ThriftClient, ForsunPlanError
from ..utils import parse_cmd, string_type, unicode_type

parser = argparse.ArgumentParser(description='High-performance timing scheduling service')
parser.add_argument('--host', dest='host', default="127.0.0.1", help='host (default: 127.0.0.1)')
parser.add_argument('--port', dest='port', default=6458, type=int, help='port (default: 6458)')
parser.add_argument('--exe', dest='execute', default='', type=str, help='execute cmd (default: )')
parser.add_argument('cmd', default='', type=str, nargs=argparse.OPTIONAL, help='execute cmd (default: )')

client = None

def print_plan(plan):
    times = []
    if plan.is_time_out:
        times.append("*" if plan.second == 0 else "*/%s/%s" % (plan.second, plan.count))
        times.append("*" if plan.minute == 0 else "*/%s/%s" % (plan.minute, plan.count))
        times.append("*" if plan.hour == 0 else "*/%s/%s" % (plan.hour, plan.count))
        times.append("*" if plan.day == 0 else "*/%s/%s" % (plan.day, plan.count))
        times.append("*" if plan.month == 0 else "*/%s/%s" % (plan.month, plan.count))
        times.append("*" if plan.week == -1 else "*/%s/%s" % (plan.week, plan.count))
    else:
        times.append("*" if plan.second == -1 else str(plan.second))
        times.append("*" if plan.minute == -1 else str(plan.minute))
        times.append("*" if plan.hour == -1 else str(plan.hour))
        times.append("*" if plan.day == -1 else str(plan.day))
        times.append("*" if plan.month == -1 else str(plan.month))
        times.append("*" if plan.week == -1 else str(plan.week))

    params = ";".join(["%s=%s" % (key, ("'%s'" % value) if isinstance(value, string_type) else value) for key, value in plan.params.items()])

    print(str(datetime.datetime.fromtimestamp(plan.next_time).replace(tzinfo=pytz.UTC).astimezone(tzlocal.get_localzone())),
          plan.key, " ".join(times), plan.action, '"' + params + '"')

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

def cmd_version(*args):
    print(version)

def cmd_ls(prefix = None, *args):
    keys = client.get_keys(prefix or '')
    for key in keys:
        try:
            plan = client.get(key)
            print_plan(plan)
        except ForsunPlanError:
            pass

def cmd_current(*args):
    plans = client.get_current()
    for plan in plans:
        print_plan(plan)

def cmd_time(ts = None, *args):
    if not ts:
        ts = int(time.mktime(time.gmtime()))
    elif ts.isdigit():
        ts = int(ts)
    else:
        ts = int(time.mktime(datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.UTC).timetuple()))
    plans = client.get_time(ts)
    for plan in plans:
        print_plan(plan)

def cmd_get(key, *args):
    plan = client.get(key)
    print_plan(plan)

def cmd_rm(key, *args):
    client.remove(key)
    print('success')

def cmd_set(key, seconds, minutes, hours, days, months, weeks, action, params_str, *args):
    is_timeout = False
    for ct in [seconds, minutes, hours, days, months, weeks]:
        if ct.startswith("*/"):
            is_timeout = True
            break

    if action in ("sh", "bash"):
        action = "shell"

    params = {}
    for cmd, args in parse_cmd(params_str):
        if isinstance(cmd, tuple):
            params[cmd[0]] = cmd[1]
        else:
            params[cmd] = args

    if action == "shell":
        if "cmd" not in params:
            params = {"cmd": params_str}
    elif action == "http":
        if "url" not in params:
            params = {"url": params_str}

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
        seconds = int(seconds) if seconds != "*" else -1
        minutes = int(minutes) if minutes != "*" else -1
        hours = int(hours) if hours != "*" else -1
        days = int(days) if days != "*" else -1
        months = int(months) if months != "*" else -1
        weeks = int(weeks) if weeks != "*" else -1

        plan = client.create(key, seconds, minutes, hours, days, months, weeks, action, params)

    print_plan(plan)

def cmd_info(*args):
    info = client.info()

    keys = [
        "python_version",
        "forsun_version",
        "start_time",
        "cpu_user",
        "cpu_system",
        "mem_rss",
        "mem_vms",
        "current_time",
        "",

        "stores",
        "current_store",
        "actions",
        "bind_port",
        "http_bind_port",
        "extensions",
        "",

        "connecting_count",
        "connected_count",
        "requesting_count",
        "requested_count",
        "requested_error_count",
        "",

        "http_connecting_count",
        "http_connected_count",
        "http_requesting_count",
        "http_requested_count",
        "http_requested_error_count",
        "",

        "created_count",
        "create_timeouted_count",
        "removed_count",
        "plan_count",
        "timeout_handling_count",
        "timeout_handled_count",
        "",

        "action_executing_count",
        "action_executed_count",
        "action_executed_error_count",
        "action_retried_count",
        "",

        "timer_loop_count",
        "timer_loop_ready_error_count",
        "",
    ]

    for key in keys:
        if key in ("mem_rss", "mem_vms"):
            value, unit = int(info.get(key), 0), "B"
            for unit in ["B", "K", "M", "G"]:
                if value < 1024:
                    break
                value = float(value) / 1024.0

            print(key + ":\t" + ("%.2f" % value) + unit)
            continue

        if key == "current_time":
            print(key + ":\t" + str(datetime.datetime.fromtimestamp(int(info.get(key), 0)).replace(tzinfo=pytz.UTC).astimezone(tzlocal.get_localzone())))
            continue

        print((key + ":\t" + info.get(key)) if key else "")

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
        'version': cmd_version,

        'ls': cmd_ls,
        'current': cmd_current,
        'time': cmd_time,
        'get': cmd_get,
        'rm': cmd_rm,
        'set': cmd_set,
        'info': cmd_info,
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
                except ForsunPlanError as e:
                    print('cmd ForsunPlanError: ', e.code, e.message)
                    exit(1)
                except Exception as e:
                    print('cmd error: ', e)
                    exit(1)
        exit(0)

    print('Welcome to the Forsun', version)
    print("Type 'help' for help")
    print('')

    while True:
        try:
            command = input("forsun> ")
            cmds = parse_cmd(command)
            for cmd, params in cmds:
                if cmd not in CMDS:
                    print('Unknown cmd ', cmd)
                else:
                    try:
                        CMDS[cmd](*params)
                        print('')
                    except KeyboardInterrupt:
                        break
                    except ForsunPlanError as e:
                        print('cmd ForsunPlanError: ', e.code, e.message)
                    except Exception as e:
                        print('cmd error: ', e)
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()