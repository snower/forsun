# -*- coding: utf-8 -*-
# 15/6/27
# create by: snower

import time
import logging
from tornado import gen
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from ..action import Action, ExecuteActionError
from ... import config
from ...error import ActionExecuteRetry

class HttpAction(Action):
    def __init__(self, *args, **kwargs):
        super(HttpAction, self).__init__(*args, **kwargs)

        self.client = AsyncHTTPClient()
        self.start_time = time.time()
        self.configed = False

    def config(self):
        import forsun
        AsyncHTTPClient.configure(None,
                                  max_clients=config.get("ACTION_HTTP_MAX_CLIENTS", 64),
                                  defaults={"user_agent": config.get("ACTION_HTTP_USER_AGENT") or ("forsun/%s" % forsun.version)
                                  })
        self.configed = True

    @gen.coroutine
    def execute(self, *args, **kwargs):
        if not self.configed:
            self.config()

        if not self.params:
            raise ExecuteActionError("url is empty")

        url = self.params["url"]
        method = self.params.get("method", 'GET')
        if method.lower() not in ("get", "post", "put", "delete", "head"):
            method= 'GET'

        body = self.params.get('body', None)
        headers = {}
        for key in self.params:
            if key.startswith("header_"):
                headers[key[7:]] = self.params[key]

        auth_username = self.params.get('auth_username', None)
        auth_password = self.params.get('auth_password', None)
        auth_mode = self.params.get('auth_mode', None)
        user_agent = self.params.get("user_agent", None)
        connect_timeout = self.params.get("connect_timeout", config.get("ACTION_HTTP_CONNECT_TIMEOUT", 5))
        request_timeout = self.params.get("request_timeout", config.get("ACTION_HTTP_REQUEST_TIMEOUT", 120))

        headers["X-FORSUN-TIMESTAMP"] = str(self.ts)
        request = HTTPRequest(url, method, body=body, headers=headers,
                              auth_username=auth_username, auth_password=auth_password, auth_mode=auth_mode,
                              user_agent = user_agent, connect_timeout=connect_timeout, request_timeout=request_timeout
        )
        response = yield self.client.fetch(request, raise_error = False)
        logging.debug("http action execute '%s' %s '%s' %s '%s' %.2fms", self.plan.key, method, url,
                      response.code, response.reason, (time.time() - self.start_time) * 1000)
        if response and response.code >= 500:
            raise ActionExecuteRetry()