# -*- coding: utf-8 -*-
# 15/6/27
# create by: snower

import time
import datetime
import struct
import msgpack
import pytz
from . import config

if config.get("STORE_DRIVER") == 'redis':
    server_id = int(config.get("STORE_REDIS_SERVER_ID"))
else:
    server_id = 0

class Plan(object):
    count_index = 0

    def __init__(self, key, second=0, minute = -1, hour = -1, day = -1, month = -1, week = -1, status = 0, count=0, is_time_out=False, next_time=None, current_count=0, last_timeout=0, created_time=0, action="event", params="{}"):
        self.key = key
        self.is_time_out = is_time_out
        self.second = second
        self.minute = minute
        self.hour = hour
        self.day = day
        self.month = month
        self.week = week
        self.status = status
        self.count = count
        self.current_count = int(current_count)
        self.last_timeout = int(last_timeout)
        self.created_time = float(created_time)
        self.action = action
        self.params = params

        if not self.key:
            self.key = self.gen_key()

        if self.is_time_out:
            self.get_timeout()
        else:
            self.get_plan()

        self.next_time = self.get_next_time() if not next_time or int(next_time) <= time.mktime(time.gmtime()) else int(next_time)

    def gen_key(self):
        self.__class__.count_index += 1
        return struct.pack("!III", self.created_time, server_id, self.count_index).encode("hex")

    def get_timeout(self):
        self.timeout_time = self.second if self.second >= 0 else 0
        self.timeout_time += self.minute * 60 if self.minute >= 0 else 0
        self.timeout_time += self.hour * 60 * 60 if self.hour >= 0 else 0
        self.timeout_time += self.day * 24 * 60 * 60 if self.day >= 0 else 0
        self.timeout_time += self.month * 30 * 24 * 60 * 60 if self.month >= 0 else 0
        self.timeout_time += self.week * 7 * 24 * 60 * 60 if self.week >= 0 else 0

    def get_plan(self):
        now = datetime.datetime.now(pytz.UTC)
        self.start_time = datetime.datetime(
            now.year,
            now.month if self.month == -1 else self.month,
            1 if self.day == -1 else self.day,
            0 if self.hour == -1 else self.hour,
            0 if self.minute == -1 else self.minute,
            0 if self.second == -1 else self.second,
            tzinfo=pytz.UTC,
        )

        self.step_time = None
        for pt in ["second", "minute", "hour", "day", "month"]:
            if getattr(self, pt) == -1:
                if pt != "month":
                    self.step_time = datetime.timedelta(**{pt+"s":1})
                else:
                    self.step_time = 1
                break

    def check(self, current_time):
        for pt in ["second", "minute", "hour", "day", "month"]:
            if getattr(self, pt) != -1 and getattr(self, pt) != getattr(current_time, pt):
                return False
        return True

    def get_next_time(self):
        if self.count != 0 and self.current_count >= self.count:
            return None

        if self.is_time_out:
            return int(time.mktime(time.gmtime())) + self.timeout_time
        else:
            now = datetime.datetime.now(pytz.UTC)
            if self.start_time >= now:
                return int(time.mktime(self.start_time.timetuple()))
            if self.start_time < now and self.step_time is None:
                return None
            current_time = self.start_time
            while not self.check(current_time) or current_time < now:
                if isinstance(self.step_time, int):
                    current_time = datetime.datetime(current_time.year if current_time.month < 12 else current_time.year + 1,
                                                     current_time.month + 1 if current_time.month < 12 else 1, current_time.day,
                                                     current_time.hour, current_time.minute, current_time.second,
                                                     tzinfo=pytz.UTC)
                else:
                    current_time += self.step_time
            return int(time.mktime(current_time.timetuple()))

    def dumps(self):
        return msgpack.dumps({
            "key": self.key,
            "second": self.second,
            "minute": self.minute,
            "hour": self.hour,
            "day": self.day,
            "month": self.month,
            "week": self.week,
            "status": self.status,
            "count": self.count,
            "is_time_out": self.is_time_out,
            "next_time": self.next_time,
            "current_count": self.current_count,
            "last_timeout": self.last_timeout,
            "created_time": self.created_time,
            "action": self.action,
            "params": self.params,
        })

    @classmethod
    def loads(cls, data):
        data = msgpack.loads(data, encoding = "utf-8")
        return cls(**data)

    def __str__(self):
        return "Plan('%s', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)" % \
               (self.key, self.second, self.minute, self.hour, self.day, self.month, self.week, self.status,
                self.count, self.is_time_out, self.next_time, self.current_count, self.last_timeout)