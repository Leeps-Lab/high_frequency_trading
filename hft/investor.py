from .trader import ELOTrader
from .orderstore import OrderStore
from .utility import format_message
from collections import deque
import itertools

class InvestorFactory:
    @staticmethod
    def get_model(market):
        return ELOInvestor(market)


class ELOInvestor(ELOTrader):
    model_name = 'inv'

    message_dispatch = { 
        'A': 'accepted', 'investor_arrivals': 'invest',
        'E': 'executed', 'C': 'canceled'}

    def __init__(self, market):
        self.subsession_id = market.subsession_id
        self.player_id = market.market_id
        self.exchange_host = market.exchange_host
        self.exchange_port = market.exchange_port
        self.orderstore = OrderStore(
            self.player_id, market.id_in_subsession, token_prefix='INV')
        self.outgoing_messages = deque()

    def invest(self, **kwargs):
        order_info = self.orderstore.enter(**kwargs)
        message_content = {'host': self.exchange_host, 'port': self.exchange_port, 
            'type': 'enter', 'delay': 0.01, 'order_info': order_info}
        internal_message = format_message('exchange', **message_content)
        self.outgoing_messages.append(internal_message)

    def executed(self, **kwargs):
        order_info =  self.orderstore.confirm('executed', **kwargs)
        buy_sell_indicator = order_info['buy_sell_indicator']
        price = order_info['price']
        order_token = kwargs['order_token']
        execution_price = kwargs['execution_price']
        self.event.broadcast_msgs('executed', price=price, order_token=order_token,
            cash=0, player_id=self.player_id, market_id=self.player_id, execution_price=execution_price,
            inventory=self.orderstore.inventory, buy_sell_indicator=buy_sell_indicator)
        return order_info