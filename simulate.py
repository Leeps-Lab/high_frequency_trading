from simulations.trader_bot import TraderBot
from simulations import trader_client
from twisted.internet import reactor
from simulations.utility import MockMarket

EXCHANGE_HOST = '127.0.0.1'
EXCHANGE_PORT = 9001

SESSION_DURATION = 60
HISTORY_DUMP_FILE = 'session_config/exogenous_events/test.csv'
RANDOM_ORDER_FILE = 'simulations/inputs/random_order_inputs_set_2.csv'

def run():
    trader = TraderBot(session_duration=SESSION_DURATION, 
                        random_order_file=RANDOM_ORDER_FILE)
    market = MockMarket(session_duration=SESSION_DURATION, 
                        dump_path=HISTORY_DUMP_FILE)
    factory = trader_client.MyConnectionFactory(trader, market)
    reactor.connectTCP(EXCHANGE_HOST, EXCHANGE_PORT, factory)
    reactor.run()

if __name__ == '__main__':
    run()
