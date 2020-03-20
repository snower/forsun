# -*- coding: utf-8 -*-
# 15/6/27
# create by: snower

from __future__ import absolute_import, division, print_function, with_statement

import os
import sys
import argparse
import multiprocessing
import atexit
from ..forsun import config
from ..utils import is_py3

parser = argparse.ArgumentParser(description='High-performance timing scheduling service')
parser.add_argument('--conf', dest='conf', default="", help='conf filename')
parser.add_argument('--bind', dest='bind_host', default="", help='bind host (default: 127.0.0.1)')
parser.add_argument('--port', dest='bind_port', default=0, type=int, help='bind port (default: 6458)')
parser.add_argument('--http', dest='http_bind', default="", help='bind http server (default: ) example: 127.0.0.1:80')
parser.add_argument('--demon', dest='demon', nargs='?', const=True, default=False, type=bool, help='run demon mode')
parser.add_argument('--nodemon', dest='nodemon', nargs='?', const=True, default=False, type=bool, help='run no demon mode')
parser.add_argument('--log', dest='log_file', default='', type=str, help='log file')
parser.add_argument('--log-level', dest='log_level', default='', type=str, help='log level (defaul: INFO)')
parser.add_argument('--driver', dest='driver', default='', type=str, help='store driver mem or redis (defaul: mem)')
parser.add_argument('--driver-mem-store-file', dest='store_mem_store_file', default='', type=str, help='store mem driver store file (defaul: ~/.forsun.dump)')
parser.add_argument('--driver-redis-host', dest='driver_redis_host', default='', type=str, help='store reids driver host (defaul: 127.0.0.1)')
parser.add_argument('--driver-redis-port', dest='driver_redis_port', default=0, type=int, help='store reids driver port (defaul: 6379)')
parser.add_argument('--driver-redis-db', dest='driver_redis_db', default=0, type=int, help='store reids driver db (defaul: 0)')
parser.add_argument('--driver-redis-password', dest='driver_redis_password', default='', type=str, help='store reids driver password (defaul: )')
parser.add_argument('--driver-redis-prefix', dest='driver_redis_prefix', default='', type=str, help='store reids driver key prefix (defaul: forsun)')
parser.add_argument('--driver-redis-server-id', dest='driver_redis_server_id', default=0, type=int, help='store reids driver server id (defaul: 0)')
parser.add_argument('--extension-path', dest='extension_path', default='', type=str, help='extension path')
parser.add_argument('--extension', dest='extensions', default=[], action="append", type=str, help='extension name')

def main():
    args = parser.parse_args()

    if args.conf:
        try:
            config.load_conf(args.conf)
        except Exception as e:
            print("load conf file error ", str(e))
            exit(1)

    if args.log_file:
        config.set("LOG_FILE", args.log_file)
    if args.log_level:
        config.set("LOG_LEVEL", args.log_level)

    if args.bind_host:
        config.set("BIND_ADDRESS", args.bind_host)
    if args.bind_port:
        config.set("PORT", args.bind_port)
    if args.http_bind:
        config.set("HTTP_BIND", args.http_bind)

    if args.driver:
        config.set("STORE_DRIVER", args.driver)
    if args.store_mem_store_file:
        config.set("STORE_MEM_STORE_FILE", args.store_mem_store_file)
    if args.driver_redis_host:
        config.set("STORE_REDIS_HOST", args.driver_redis_host)
    if args.driver_redis_port:
        config.set("STORE_REDIS_PORT", args.driver_redis_port)
    if args.driver_redis_db:
        config.set("STORE_REDIS_DB", args.driver_redis_db)
    if args.driver_redis_password:
        config.set("STORE_REDIS_PASSWORD", args.driver_redis_password)
    if args.driver_redis_prefix:
        config.set("STORE_REDIS_PREFIX", args.driver_redis_prefix)
    if args.driver_redis_server_id:
        config.set("STORE_REDIS_SERVER_ID", args.driver_redis_server_id)

    if args.extension_path:
        config.set("EXTENSION_PATH", args.extension_path)
    if args.extensions:
        config.set("EXTENSIONS", args.extensions)


    if not args.nodemon:
        from ..forsun import Forsun

        def on_start(forsun):
            print("forsund started by pid %s" % p.pid)
            sys.stdin.close()
            sys.stdin = open(os.devnull)

            sys.stdout.close()
            sys.stdout = open(os.devnull, 'w')

            sys.stderr.close()
            sys.stderr = open(os.devnull, 'w')

        def run():
            try:
                forsun = Forsun()
                forsun.serve(on_start)
            except Exception as e:
                print(e)
                exit(1)

        p = multiprocessing.Process(target = run, name=" ".join(sys.argv))
        p.start()
        if is_py3:
            atexit._clear()
        else:
            atexit._exithandlers = []
    else:
        try:
            from ..forsun import Forsun
            forsun = Forsun()
            forsun.serve()
        except Exception as e:
            print(e)
            exit(1)

if __name__ == "__main__":
    main()