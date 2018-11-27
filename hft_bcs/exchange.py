
import sys
import logging
import time
from twisted.internet.protocol import Protocol, ClientFactory
import numpy as np
from twisted.internet import reactor
from .hft_logging import session_events as hfl
from collections import deque

log = logging.getLogger(__name__)

class OUCH(Protocol):
    bytes_needed = {
        'S': 10,
        'E': 40,
        'C': 28,
        'U': 80,
        'A': 66
    }

    def __init__(self):
        super()
        self.buffer = deque()

    def connectionMade(self):
        log.debug('connection made.')
      
    def dataReceived(self, data):
        cls = self.__class__
        header = chr(data[0])
        try:
            bytes_needed = cls.bytes_needed[header]
        except KeyError:
             raise ValueError('unknown header %s.' % header)

        if len(data) >= bytes_needed:
            remainder = bytes_needed
            self.buffer.extend(data[:remainder])
            data = data[remainder:]
            try:
                self.factory.group.receive_from_exchange(bytes(self.buffer))
                self.buffer.clear()
            except AttributeError as e:
                log.exception(e)

        if len(data):
            self.dataReceived(data)

    def sendMessage(self, msg, delay):
        if not isinstance(msg, bytes):
            msg = msg.tobytes()
        # can receive a message back (accepted),
        # can receive 2 messages (accepted, executed),
        # can receive 0 message (replace dying silently).
        reactor.callLater(delay, self.transport.write, msg)


class OUCHConnectionFactory(ClientFactory):
    protocol = OUCH

    def __init__(self, group, addr):
        super()
        self.group = group
        self.addr = addr
        self.connection = None

    def buildProtocol(self, addr):
        l = 'connecting to exchange server at %s' % addr
        hfl.log_events.push(hfl.exchange, **{'context': l})
        self.connection = ClientFactory.buildProtocol(self, addr)
        return self.connection

    def clientConnectionLost(self, connector, reason):
        l = 'lost connection to exchange at %s: %s' % (self.addr, reason)
        log.debug(l)
        hfl.log_events.push(hfl.exchange, **{'context': l})

    def clientConnectionFailed(self, connector, reason):
        log.debug('failed to connect to exchange at %s: %s' % (self.addr, reason))


exchanges = {}

def connect(group, host, port, wait_for_connection=False):
    addr = '{}:{}'.format(host, port)
    if addr not in exchanges:
        factory = OUCHConnectionFactory(group, addr)
        exchanges[addr] = factory
        reactor.connectTCP(host, port, factory)
    else:
        if exchanges[addr].group != group:
            log.info('exchange at {} already has a group: {}'.format(addr, exchanges))
        exchanges[addr].group = group
    while not exchanges[addr].connection and wait_for_connection:
        log.info('waiting for connection to %s...' % addr)
        time.sleep(0.1)
    return exchanges[addr]


def disconnect(group, host, port):
    addr = '{}:{}'.format(host, port)
    try:
        conn = exchanges[addr].connection
    except KeyError:
        log.warning('connection at %s not found.', addr)
    else:
        conn.transport.loseConnection()
        del exchanges[addr]

def send_exchange(host, port, message, delay):
    addr = '{}:{}'.format(host, port)
    if addr not in exchanges:
        raise FileNotFoundError('connection at %s not found.', addr)
    conn = exchanges[addr].connection
    conn.sendMessage(message, delay)
