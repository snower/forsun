# -*- coding: utf-8 -*-
# 15/6/8
# create by: snower

import time
import signal
import logging
try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty

__time_out_callback = None
__exit_callback = None
__queues = Queue()
__is_stop = False
__current_time = int(time.mktime(time.gmtime()))

def exit_handler(signum, frame):
    __queues.put((__exit_callback, tuple()), False)

def handler(signum, frame):
    __queues.put((__time_out_callback, (int(time.mktime(time.gmtime())),)), False)

def reset():
    global __time_out_callback, __exit_callback, __queues, __is_stop, __current_time
    __time_out_callback = None
    __exit_callback = None
    __queues = Queue()
    __is_stop = False
    __current_time = int(time.mktime(time.gmtime()))

def start(callback, exit_callback):
    global __time_out_callback, __exit_callback
    __time_out_callback = callback
    __exit_callback = exit_callback

def stop():
    global __time_out_callback, __exit_callback, __is_stop
    __time_out_callback = None
    __exit_callback = None
    __is_stop = True
    logging.info("timer stoping")

def loop():
    signal.signal(signal.SIGHUP, exit_handler)
    signal.signal(signal.SIGINT, exit_handler)
    signal.signal(signal.SIGTERM, exit_handler)
    signal.signal(signal.SIGALRM, handler)
    signal.setitimer(signal.ITIMER_REAL, 1, 1)
    logging.info("timer ready")
    while not __is_stop:
        try:
            callback, args = __queues.get(True, 1)
            if callback:
                callback(*args)
        except Empty:
            continue

def current():
    return __current_time