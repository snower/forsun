# -*- coding: utf-8 -*-
# 18/8/29
# create by: snower

import sys
import os
import datetime
import tzlocal
import psutil
from .version import version

current_tz = tzlocal.get_localzone()

class ForsunStatus(object):
    def __init__(self):
        self.start_time = datetime.datetime.now(current_tz)
        self.connecting_count = 0
        self.connected_count = 0
        self.requesting_count = 0
        self.requested_count = 0
        self.requested_error_count = 0
        self.http_connecting_count = 0
        self.http_connected_count = 0
        self.http_requesting_count = 0
        self.http_requested_count = 0
        self.http_requested_error_count = 0
        self.created_count = 0
        self.create_timeouted_count = 0
        self.removed_count = 0
        self.plan_count = 0
        self.timeout_handling_count = 0
        self.timeout_handled_count = 0
        self.action_executing_count = 0
        self.action_executed_count = 0
        self.action_executed_error_count = 0
        self.action_retried_count = 0
        self.timer_loop_count = 0
        self.timer_loop_ready_error_count = 0
        self.customs = {}

    def inc(self, key, value = 1):
        if key not in self.customs:
            self.customs[key] = value
        else:
            self.customs[key] += value
        
    def get_info(self):
        from .store import get_store_names
        from .action import get_driver_names
        from .timer import current
        from . import config

        process = psutil.Process(os.getpid())
        cpu_times = process.cpu_times()
        memory_info = process.memory_info()

        info = {
            "python_version": sys.version.replace("\n", " "),
            "forsun_version": version,
            "start_time": str(self.start_time),
            "cpu_user": str(cpu_times.user),
            "cpu_system": str(cpu_times.system),
            "mem_rss": str(memory_info.rss),
            "mem_vms": str(memory_info.vms),
            "current_time": str(current()),

            "stores": ";".join(get_store_names()),
            "current_store": config.get("STORE_DRIVER", ""),
            "actions": ";".join(get_driver_names()),
            "bind_port": "%s:%s" % (config.get("BIND_ADDRESS", ""), config.get("PORT", "")),
            "http_bind_port": config.get("HTTP_BIND", ""),
            "extensions": ";".join(config.get("EXTENSIONS", [])),

            "connecting_count": str(self.connecting_count),
            "connected_count": str(self.connected_count),
            "requesting_count": str(self.requesting_count),
            "requested_count": str(self.requested_count),
            "requested_error_count": str(self.requested_error_count),
            "http_connecting_count": str(self.http_connecting_count),
            "http_connected_count": str(self.http_connected_count),
            "http_requesting_count": str(self.http_requesting_count),
            "http_requested_count": str(self.http_requested_count),
            "http_requested_error_count": str(self.http_requested_error_count),
            "created_count": str(self.created_count),
            "create_timeouted_count": str(self.create_timeouted_count),
            "removed_count": str(self.removed_count),
            "plan_count": str(self.plan_count),
            "timeout_handling_count": str(self.timeout_handling_count),
            "timeout_handled_count": str(self.timeout_handled_count),
            "action_executing_count": str(self.action_executing_count),
            "action_executed_count": str(self.action_executed_count),
            "action_executed_error_count": str(self.action_executed_error_count),
            "action_retried_count": str(self.action_retried_count),

            "timer_loop_count": str(self.timer_loop_count),
            "timer_loop_ready_error_count": str(self.timer_loop_ready_error_count),
        }

        for key, value in self.customs.items():
            info[key] = str(value)

        return info

forsun_status = ForsunStatus()