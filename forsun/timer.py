# -*- coding: utf-8 -*-
# 15/6/8
# create by: snower

import time
import signal
import traceback
import logging
import threading
from collections import deque
from .status import forsun_status

__time_out_callback = None
__exit_callback = None
__queues = deque()
__queue_ready_event = threading.Event()
__is_stop = False
__current_time = int(time.mktime(time.gmtime()))
__time_offset = int(time.time() - __current_time)

def exit_handler(signum, frame):
    __queues.append((__exit_callback, tuple()))
    if not __queue_ready_event.is_set():
        __queue_ready_event.set()
    else:
        forsun_status.timer_loop_ready_error_count += 1

def handler(signum, frame):
    global __current_time
    __current_time = int(time.time() - __time_offset)
    __queues.append((__time_out_callback, (__current_time,)))
    if not __queue_ready_event.is_set():
        __queue_ready_event.set()
    else:
        forsun_status.timer_loop_ready_error_count += 1

def reset():
    global __time_out_callback, __exit_callback, __queues, __queue_ready_event, __is_stop, __current_time
    __time_out_callback = None
    __exit_callback = None
    __queues = deque()
    __queue_ready_event = threading.Event()
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
            if __queues:
                callback, args = __queues.popleft()
                if callback and callable(callback):
                    callback(*args)
                continue

            if __queue_ready_event.is_set():
                __queue_ready_event.clear()

            if not __queues:
                __queue_ready_event.wait(1.3)
            forsun_status.timer_loop_count += 1
        except KeyboardInterrupt:
            if __exit_callback and callable(__exit_callback):
                __exit_callback()
        except Exception as e:
            logging.info("timer error %s\n%s", e, traceback.format_exc())

            if __exit_callback and callable(__exit_callback):
                __exit_callback()

def current():
    return __current_time