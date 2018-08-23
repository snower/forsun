# -*- coding: utf-8 -*-
# 18/2/7
# create by: snower

import time
import logging
from tornado import gen
from tormysql.helpers import ConnectionPool
from ..action import Action, ExecuteActionError
from ... import config
from ...error import ActionExecuteRetry

class MysqlAction(Action):
    client_pools = {}

    def __init__(self, *args, **kwargs):
        super(MysqlAction, self).__init__(*args, **kwargs)

        self.start_time  = time.time()

    def get_client(self, host, port, db, user, passwd, max_connections):
        key = "%s:%s:%s:%s" % (host, port, db, user)
        if key not in self.client_pools:
            wait_connection_timeout = int(config.get("ACTION_MYSQL_WAIT_CONNECTION_TIMEOUT", 7200))
            idle_seconds = int(config.get("ACTION_MYSQL_IDLE_SECONDS", 120))
            self.__class__.client_pools[key] = ConnectionPool(host = host, port = port, db = db,
                                                              user = user, passwd = passwd,
                                                              max_connections = max_connections,
                                                              wait_connection_timeout = wait_connection_timeout,
                                                              idle_seconds = idle_seconds,
                                                            )
        return self.__class__.client_pools[key]

    @gen.coroutine
    def execute(self, *args, **kwargs):
        if len(self.params) < 4:
            raise ExecuteActionError("redis params is empty")

        host = self.params.get("host", "127.0.0.1")
        port = int(self.params.get("port", 3306))
        db = self.params.get("db", 'mysql')
        user = self.params.get("user", config.get("ACTION_MYSQL_USER", 'root'))
        passwd = self.params.get("passwd", config.get("ACTION_MYSQL_PASSWD", ''))
        max_connections = int(self.params.get("max_connections", config.get("ACTION_MYSQL_MAX_CONNECTIONS", 8)))
        sql = self.params.get("sql")

        if not sql:
            logging.error("mysql action execute error %s sql is empty", self.plan.key)
            raise gen.Return(None)

        try:
            client = self.get_client(host, port, db, user, passwd, max_connections)
            tx = yield client.begin()
            try:
                yield tx.execute(sql)
            except Exception as e:
                yield tx.rollback()
                logging.error("mysql action execute error '%s' %s %s:%s/%s '%s' '%s' %.2fms", self.plan.key, user, host,
                              port, db, sql, e, (time.time() - self.start_time) * 1000)
            else:
                yield tx.commit()
                logging.debug("mysql action execute '%s' %s %s:%s/%s '%s' %.2fms", self.plan.key, user, host, port, db,
                              sql, (time.time() - self.start_time) * 1000)
        except Exception as e:
            logging.error("mysql action execute error '%s' %s %s:%s/%s '%s' '%s' %.2fms", self.plan.key, user, host,
                          port, db, sql, e, (time.time() - self.start_time) * 1000)
            raise ActionExecuteRetry()