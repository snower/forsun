# -*- coding: utf-8 -*-
# 15/6/27
# create by: snower

import os
import time
import subprocess
import shlex
import threading
import json
import logging
from tornado import gen
from ..action import Action, ExecuteActionError

class ShellAction(Action):
    def __init__(self, *args, **kwargs):
        super(ShellAction, self).__init__(*args, **kwargs)

        self.start_time = time.time()

    @classmethod
    def init(cls):
        pass

    @gen.coroutine
    def execute(self, *args, **kwargs):
        if not self.params:
            raise ExecuteActionError("cmd is empty")

        cmd = self.params[0]
        args = self.params[1] if len(self.params) >= 2 else ""
        env = self.params[2] if len(self.params) >= 3 else '{}'
        if env:
            try:
                env = json.loads(env)
            except:
                env = {}
        options = self.params[3] if len(self.params) >= 4 else '{}'
        if options:
            try:
                options = json.loads(options)
            except:
                options = {}
        env["FORSUN_TIMESTAMP"] = str(self.ts)
        log_file_name = options.get("log_file", None)

        def run():
            log_fp = None
            if log_file_name:
                try:
                    log_fp = open(log_file_name, "wa+")
                except:pass

            try:
                sh = "%s %s"  % (cmd, args)
                p = subprocess.Popen(shlex.split(sh), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True, env=env)
                while True:
                    line = p.stdout.readline()
                    if line and log_fp:
                        log_fp.write(line)
                    try:
                        os.waitpid(p.pid, os.WNOHANG)
                    except OSError:
                        line = p.stdout.read()
                        if line and log_fp:
                            log_fp.write(line)
                        break
                    time.sleep(0.5)
                logging.info("shell action %s exit %.2fms", cmd, (time.time() - self.start_time) * 1000)
            finally:
                if log_file_name and log_fp:
                    log_fp.close()

        t = threading.Thread(target=run)
        t.setDaemon(True)
        t.start()