from hft.trader import ELOInvestor
from hft.event import ELOEvent
from .utility import MockWSMessage, generate_random_test_orders
import logging

log = logging.getLogger(__name__)

ws_message_defaults = {
    'subsession_id': 0,  'market_id': 0, 'player_id': 0,
    'type': 'investor_arrivals'}

NUM_ORDERS = 60
SESSION_DURATION = 60

class TraderBot:

    default_trader_model_args = (0, 0, 0, 1, 'investor', 0, 0)
    message_class = MockWSMessage
    required_message_fields = ('price', 'buy_sell_indicator', )
    trader_model_cls = ELOInvestor

    def __init__(self):
        self.trader_model = self.trader_model_cls(
            *self.default_trader_model_args)
        self.random_order_generator = generate_random_test_orders(
                                        NUM_ORDERS, SESSION_DURATION)
        self.exchange_connection = None

    @property
    def exchange_connection(self):
        return self.__exchange_connection

    @exchange_connection.setter
    def exchange_connection(self, conn):
        self.__exchange_connection = conn

    def run(self):
        try:
            while True:
                new_order = self.generate_order()
                self.enter_order(new_order, new_order['arrival_time'])
        except StopIteration:
            log.debug('all orders are scheduled.')

    def handle_event(self, event):
        self.trader_model.handle_event(event)

    def generate_order(self, *args, **kwargs):
        new_order = next(self.random_order_generator)
        for field in self.required_message_fields:
            if field not in new_order:
                raise Exception('key %s is missing in %s' % (field, new_order))
            else:
                return new_order

    def enter_order(self, order, delay):
        message = MockWSMessage(order, **ws_message_defaults)
        event = ELOEvent('random_order', message)
        self.trader_model.handle_event(event)
        while event.exchange_msgs:
            message = event.exchange_msgs.pop()
            if self.exchange_connection is not None:
                self.exchange_connection.sendMessage(message.translate(), delay)
            else:
                raise Exception('exchange connection is none.')
