from simulations.trader_bot import TraderBot
from simulations import trader_client
from twisted.internet import reactor
from simulations.utility import MockMarket

EXCHANGE_HOST = '127.0.0.1'
EXCHANGE_PORT = 9001


def run():
    trader = TraderBot()
    market = MockMarket()
    factory = trader_client.MyConnectionFactory(trader, market)
    reactor.connectTCP(EXCHANGE_HOST, EXCHANGE_PORT, factory)
    reactor.run()

if __name__ == '__main__':
    run()
