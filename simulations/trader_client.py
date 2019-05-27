from hft.exchange import OUCH
from twisted.internet.protocol import ClientFactory
from .trader_bot import TraderBot
from hft.incoming_message import IncomingOuchMessage
from hft.event import ELOEvent
from .utility import incoming_message_defaults
import logging

logging.basicConfig(format='%(asctime)s %(message)s', 
                    datefmt='%m/%d/%Y %I:%M:%S %p', 
                    level=logging.DEBUG)

log = logging.getLogger(__name__)


class MyOuch(OUCH):

    def connectionMade(self):
        log.info('connected to exchange.')
        self.factory.trader.exchange_connection = self
        self.factory.market.reset()
        self.factory.trader.run()

    def handle_incoming_data(self, header):
        msg = IncomingOuchMessage(
            bytes(self.buffer), **incoming_message_defaults)
        event = ELOEvent('exchange', msg)
        self.factory.market.handle_event(event)
        self.factory.trader.handle_event(event)


class MyConnectionFactory(ClientFactory):
    protocol = MyOuch

    def __init__(self, trader, market):
        super()
        self.connection = None
        self.trader = trader
        self.market = market

    def buildProtocol(self, addr):
        log.info('connecting to exchange server at %s' % addr)
        self.connection = ClientFactory.buildProtocol(self, addr)
        return self.connection

    def clientConnectionLost(self, connector, reason):
        log.info('lost connection to exchange')

    def clientConnectionFailed(self, connector, reason):
        log.debug('failed to connect to exchange')
