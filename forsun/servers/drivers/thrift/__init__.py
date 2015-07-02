# -*- coding: utf-8 -*-
# 15/6/27
# create by: snower

import logging
import threading
from tornado.ioloop import IOLoop
from torthrift.protocol import TBinaryProtocolFactory
from torthrift.transport import TIOStreamTransportFactory
from torthrift.server import TTornadoServer
from ...server import Server
from processor.Forsun import Processor
from handler import Handler
from .... import config

class ThriftServer(Server):
    def __init__(self, *args, **kwargs):
        super(ThriftServer, self).__init__(*args, **kwargs)

        self.server = None
        self.thread = None

    def serve(self):
        handler = Handler(self.forsun)
        processor = Processor(handler)
        tfactory = TIOStreamTransportFactory()
        protocol = TBinaryProtocolFactory()

        bind_address = config.get("SERVER_THRIFT_BIND_ADDRESS", "127.0.0.1")
        port = config.get("SERVER_THRIFT_PORT", 5643)
        self.server = TTornadoServer(processor, tfactory, protocol)
        self.server.bind(port, bind_address)
        self.server.start(1)
        ioloop = IOLoop.instance()
        logging.info("starting server by %s:%s", bind_address, port)
        ioloop.start()

    def start(self):
        self.thread = threading.Thread(target=self.serve)
        self.thread.setDaemon(True)
        self.thread.start()

    def stop(self):
        IOLoop.current().add_callback(lambda :IOLoop.current().stop())