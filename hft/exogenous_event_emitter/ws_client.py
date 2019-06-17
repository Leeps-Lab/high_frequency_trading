import sys
from twisted.internet import reactor
from autobahn.twisted.websocket import WebSocketClientFactory, WebSocketClientProtocol
from autobahn.websocket.util import parse_url
from twisted.internet.endpoints import clientFromString
from twisted.python import log
from conf import get_ws_confs, db_creds

class ExogenousEventClientProtocol(WebSocketClientProtocol):

    def __init__(self, factory, exogenous_event_emitter):
        super().__init__()
        self.factory = factory
        self.emitter = exogenous_event_emitter

    def onOpen(self):
        log.msg('connected to server.')
        self.emitter.run()
    

class ExogenousEventClientFactory(WebSocketClientFactory):

    protocol = ExogenousEventClientProtocol

    def __init__(self, emitter, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.emitter = emitter

    def buildProtocol(self, addr):
        conn = self.protocol(self, self.emitter)
        self.emitter.ws_conn = conn
        return conn


if __name__ == '__main__':
    from ws_message_emitter import WSMessageEmitter
    log.startLogging(sys.stdout)
    ws_url = sys.argv[1]
    session_id, type_code = sys.argv[2:4]
    record_code = sys.argv[4]
    emitter = WSMessageEmitter(session_id, type_code, filter_value=record_code,
        **get_ws_confs(type_code))
    emitter.read_from_db(**db_creds)
    factory = ExogenousEventClientFactory(emitter, ws_url)
    url_parsed = parse_url(ws_url)
    host, port = url_parsed[1], url_parsed[2]
    reactor.connectTCP(host, port, factory)
    reactor.run()
