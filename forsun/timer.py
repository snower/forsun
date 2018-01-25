# -*- coding: utf-8 -*-
# 15/6/8
# create by: snower

import time
import signal
import logging
from Queue import Queue, Empty

__time_out_callback = None
__time_out_queues = Queue()
__is_stop = False
__current_time = int(time.time())

def handler(signum, frame):
    __time_out_queues.put(int(time.time()), False)

def start(callback):
    global __time_out_callback, __is_stop
    __time_out_callback = callback

def stop():
    global __time_out_callback, __is_stop
    __time_out_callback = None
    __is_stop = True
    logging.info("timer stoping")

def loop():
    global __current_time, __time_out_callback

    signal.signal(signal.SIGALRM, handler)
    signal.setitimer(signal.ITIMER_REAL, 1, 1)
    logging.info("timer ready")
    while not __is_stop:
        try:
            __current_time = __time_out_queues.get(True, 0.5)
            if __time_out_callback:
                __time_out_callback(__current_time)
        except Empty:
            continue

def current():
    return __current_time