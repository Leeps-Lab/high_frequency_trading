import argparse
import logging
logging.getLogger().setLevel(logging.INFO)
import random
import string
from twisted.internet import reactor, protocol

parser = argparse.ArgumentParser(description="Mock OUCH Exchange Server")
parser.add_argument(
    '-n',
    type=int,
    default=1,
    help="Number of servers to start")


class MockOUCH(protocol.Protocol):

    def connectionMade(self):
        self.mode = 'start'
        logging.info('%s: got client connection', self.transport.getHost().port)

    def dataReceived(self, data):
        logging.info('%s: received data: %s', self.transport.getHost().port, data)
        bytes_needed = None
        if data[0] == ord('U'):
            bytes_needed = 47
        elif data[0] == ord('O'):
            bytes_needed = 49
        elif data[0] == ord('X'):
            bytes_needed = 19
        else:
            raise ValueError('Unsupported message type {}'.format(data[0]))
        for i in range(bytes_needed):
            self.transport.write(random.choice(string.ascii_letters).encode('utf-8'))


class MockFactory(protocol.Factory):
    protocol = MockOUCH


if __name__ == '__main__':
    args = parser.parse_args()
    for i in range(args.n):
        port = 9000 + i
        logging.info('starting mock server on port %d', port)
        reactor.listenTCP(port, MockFactory())
    reactor.run()