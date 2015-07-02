# -*- coding: utf-8 -*-
# 15/6/27
# create by: snower

import time
import json
import logging
from tornado import gen
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from ..action import Action, ExecuteActionError
from ... import config

class HttpAction(Action):
    def __init__(self, *args, **kwargs):
        super(HttpAction, self).__init__(*args, **kwargs)

        self.client = AsyncHTTPClient()
        self.start_time = time.time()

    @classmethod
    def init(cls):
        import forsun
        AsyncHTTPClient.configure(None,
                                  max_clients=config.get("ACTION_HTTP_MAX_CLIENTS", 64),
                                  defaults={"user_agent": config.get("ACTION_HTTP_USER_AGENT", "forsun/%s" % forsun.version)
                                  })

    @gen.coroutine
    def execute(self, *args, **kwargs):
        if not self.params:
            raise ExecuteActionError("url is empty")

        url = self.params[0]
        method = self.params[1].upper() if len(self.params) >= 2 and isinstance(self.params[1], basestring) and self.params[1].lower() in ("get", "post", "put", "delete", "head") else "GET"
        body = self.params[2] if len(self.params) >= 3 and self.params[2] else None
        headers = self.params[3] if len(self.params) >= 4 and self.params[3] else '{}'
        if headers:
            try:
                headers = json.loads(headers)
            except:
                headers = {}
        options = self.params[4] if len(self.params) >= 5 and self.params[4] else '{}'
        if options:
            try:
                options = json.loads(options)
            except:
                options = {}

        auth_username = options.get('auth_username', None)
        auth_password = options.get('auth_password', None)
        auth_mode = options.get('auth_mode', None)
        user_agent = options.get("user_agent", None)
        connect_timeout = options.get("connect_timeout", None)
        request_timeout = options.get("request_timeout", None)

        headers["X-FORSUN-TIMESTAMP"] = str(self.ts)
        request = HTTPRequest(url, method, body=body, headers=headers,
                              auth_username=auth_username, auth_password=auth_password, auth_mode=auth_mode,
                              user_agent = user_agent, connect_timeout=connect_timeout, request_timeout=request_timeout,
        )
        response = yield self.client.fetch(request)
        logging.info("http action execute %s %s %s '%s' %.2fms", method, url, response.code, response.reason, (time.time() - self.start_time) * 1000)