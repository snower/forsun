# -*- coding: utf-8 -*-
# 15/6/8
# create by: snower

import time
import signal

__time_out_callback = None
__is_stop = False
__current_time = int(time.time())

def handler(signum, frame):
    global __current_time, __time_out_callback
    __current_time = int(time.time())
    if __time_out_callback:
        __time_out_callback(__current_time)

def start(callback):
    global __time_out_callback, __is_stop
    __time_out_callback = callback

def stop():
    global __time_out_callback, __is_stop
    __time_out_callback = None
    __is_stop = True

def loop():
    signal.signal(signal.SIGALRM, handler)
    signal.setitimer(signal.ITIMER_REAL, 1, 1)
    while not __is_stop:
        time.sleep(0.1)

def current():
    return __current_time