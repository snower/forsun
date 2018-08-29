# -*- coding: utf-8 -*-
# 15/6/10
# create by: snower

import logging
import threading
from tornado.ioloop import IOLoop, asyncio
from thrift.protocol.TBinaryProtocol import TBinaryProtocolAcceleratedFactory
from torthrift.transport import TIOStreamTransportFactory
from torthrift.server import TTornadoServer as BaseTTornadoServer
from .processor.Forsun import Processor
from .handler import Handler
from .http import HTTPServer, Application
from .. import timer
from ..status import forsun_status
from .. import config

class TTornadoServer(BaseTTornadoServer):
    def process(self, *args, **kwargs):
        try:
            forsun_status.connecting_count += 1
            forsun_status.connected_count += 1
            return super(TTornadoServer, self).process(*args, **kwargs)
        finally:
            forsun_status.connecting_count -= 1

class Server(object):
    def __init__(self, forsun):
        self.forsun = forsun
        self.server = None
        self.http_server = None
        self.thread = None

    def serve_thrift(self):
        handler = Handler(self.forsun)
        processor = Processor(handler)
        tfactory = TIOStreamTransportFactory()
        protocol = TBinaryProtocolAcceleratedFactory()

        bind_address = config.get("BIND_ADDRESS", "127.0.0.1")
        port = config.get("PORT", 6458)
        self.server = TTornadoServer(processor, tfactory, protocol)
        self.server.bind(port, bind_address)
        self.server.start(1)
        logging.info("starting server by %s:%s", bind_address, port)

    def serve_http(self):
        http_bind = config.get("HTTP_BIND")
        if not http_bind:
            return

        (address, port) = http_bind.split(":")
        application = Application(self.forsun, debug=False, autoreload=False)
        self.http_server = HTTPServer(application, xheaders=True)
        self.http_server.bind(int(port), address)
        self.http_server.start(1)
        logging.info("starting http server by %s", http_bind)

    def start(self, init_callback):
        def _():
            try:
                if asyncio is not None:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                self.serve_thrift()
                self.serve_http()
                ioloop = IOLoop.instance()
                ioloop.add_callback(init_callback)
                ioloop.start()
            except Exception as e:
                logging.error("server error: %s", e)
                self.forsun.read_event.set()
                timer.stop()

        self.thread = threading.Thread(target=_)
        self.thread.setDaemon(True)
        self.thread.start()

    def stop(self):
        IOLoop.current().add_callback(lambda :IOLoop.current().stop())
        logging.info("server stoping")