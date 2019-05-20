
# GoF - Design Patterns pg.291 - State
import logging
from .utility import (MIN_BID, MAX_ASK, elo_otree_player_converter)
from .market_components.inventory import Inventory
from collections import namedtuple
from .equations import latent_bid_and_offer
from .market_components.subscription import Subscription
from .orderstore import OrderStore
from .trader_state import TraderStateFactory

log = logging.getLogger(__name__)

import time

class TraderFactory:
    @staticmethod
    def get_trader(market_environment, otree_player):
        if market_environment == 'elo':
            return ELOTrader.from_otree_player(otree_player)
        else:
            raise Exception('unknown role: %s' % market_environment)


class BaseTrader(object):

    model_name = 'trader'
    trader_state_factory = TraderStateFactory
    tracked_market_facts = ()
    otree_player_converter = elo_otree_player_converter
    orderstore_cls = OrderStore
    event_dispatch = {}
    default_delay = 0

    def __init__(self, subsession_id, market_id, player_id, id_in_market,
            default_role, exchange_host, exchange_port, cash=0, delayed=False, 
            **kwargs):
        self.subsession_id = subsession_id
        self.market_id = market_id
        self.id_in_market = id_in_market
        self.player_id = player_id
        self.exchange_host = exchange_host
        self.exchange_port = exchange_port
        self.orderstore = self.orderstore_cls(player_id, id_in_market, 
            token_prefix=kwargs.get('token_prefix', 'SUB'))
        self.inventory = Inventory()
        self.trader_role = TraderStateFactory.get_trader_state(default_role)
        self.market_facts = {k: None for k in self.tracked_market_facts}
        self.delayed = delayed
        self.staged_bid = None
        self.staged_offer = None
        self.implied_bid = None
        self.implied_offer = None
        self.disable_bid = False
        self.disable_offer = False
        self.cash = cash
        self.cost = 0
        self.net_worth = cash
    
    @classmethod
    def from_otree_player(cls, otree_player):
        args, kwargs = cls.otree_player_converter(otree_player)
        return cls(*args, **kwargs)

    def open_session(self, event):
        event_as_kws = event.to_kwargs()
        for field in self.tracked_market_facts:
            value = event_as_kws[field]
            if value is None:
                raise ValueError('%s is required to open session.' % field)
            else:    
                self.market_facts[field] = value
    
    def close_session(self, event):
        pass
    
    def handle_event(self, event):
        if event.event_type in self.event_dispatch:
            handler_name = self.event_dispatch[event.event_type]
            handler = getattr(self, handler_name)
            handler(event)
        self.trader_role.handle_event(self, event)
        return event
    
    def state_change(self, event):
        new_state = event.message.state
        trader_state = self.trader_state_factory.get_trader_state(new_state)
        self.trader_role = trader_state
        event.broadcast_msgs(
            'role_confirm', role_name=new_state, model=self)

    @property
    def delay(self):
        is_delayed_trader = self.delayed
        if is_delayed_trader is False:
            return self.default_delay
        elif is_delayed_trader is True:
            return self.__delay

    @delay.setter    
    def delay(self, order_delay_time):
        self.__delay = order_delay_time


class ELOTrader(BaseTrader):

    default_delay = 0.5
    short_delay = 0.1
    long_delay = 0.5
    tracked_market_facts = ('best_bid', 'volume_at_best_bid', 'next_bid', 'best_offer',
        'volume_at_best_offer', 'next_offer', 'signed_volume', 'e_best_bid',
        'e_best_offer', 'e_signed_volume', 'tax_rate', 'reference_price')
    event_dispatch = { 
        'market_start': 'open_session', 
        'market_end': 'close_session',
        'A': 'order_accepted', 
        'U': 'order_replaced', 
        'C': 'order_canceled', 
        'E': 'order_executed', 
        'role_change': 'state_change', 
        'slider': 'user_slider_change'}
    otree_player_converter = elo_otree_player_converter


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.technology_subscription = Subscription(
            'speed_tech', self.player_id, kwargs.get('speed_unit_cost', 0))
        self.sliders = {'slider_a_x': 0, 'slider_a_y': 0, 'slider_a_z': 0}
        self.tax_paid = 0
        self.speed_cost = 0


    def close_session(self, event):
        self.inventory.liquidify(
            event.attachments['reference_price'], 
            discount_rate=event.attachments['tax_rate'])
        self.cash += self.inventory.cash
        tax_paid = self.inventory.cost
        speed_cost = self.technology_subscription.invoice()
        self.cost += tax_paid + speed_cost
        self.tax_paid += tax_paid
        self.speed_cost += speed_cost
    
    def user_slider_change(self, event):
        self.sliders = {
            'slider_a_x': event.message.a_x, 'slider_a_y': event.message.a_y,
            'slider_a_z': event.message.a_z}       

    @property
    def best_bid_except_me(self):
        if (self.market_facts['best_bid'] == self.staged_bid and 
                self.market_facts['volume_at_best_bid'] == 1):
            return self.market_facts['next_bid']
        else:
            return self.market_facts['best_bid']      

    @property
    def best_offer_except_me(self):
        if (self.market_facts['best_offer'] == self.staged_offer and 
                self.market_facts['volume_at_best_offer'] == 1):
            return self.market_facts['next_offer']
        else:
            return self.market_facts['best_offer']

    def order_accepted(self, event):
        event_as_kws = event.to_kwargs()
        self.orderstore.confirm('enter', **event_as_kws)
        event.broadcast_msgs('confirmed', model=self, **event_as_kws)
    
    def order_replaced(self, event):
        event_as_kws = event.to_kwargs()
        order_info = self.orderstore.confirm('replaced', **event_as_kws)  
        order_token = event.message.replacement_order_token
        old_token = event.message.previous_order_token
        old_price = order_info['old_price']
        event.broadcast_msgs('replaced', order_token=order_token, 
            old_token=old_token, old_price=old_price, model=self, **event_as_kws)       

    def order_canceled(self, event):
        event_as_kws = event.to_kwargs()
        order_info = self.orderstore.confirm('canceled', **event_as_kws)
        order_token = event.message.order_token
        price = order_info['price']
        buy_sell_indicator = order_info['buy_sell_indicator']
        event.broadcast_msgs('canceled', order_token=order_token,
            price=price, buy_sell_indicator=buy_sell_indicator, 
            model=self)

    def order_executed(self, event):
        def adjust_inventory(buy_sell_indicator):
            if buy_sell_indicator == 'B':
                self.inventory.add()
            elif buy_sell_indicator == 'S':
                self.inventory.remove()
        def adjust_net_worth():
            reference_price = self.market_facts['reference_price']
            cash_value_of_stock = self.inventory.valuate(reference_price)
            self.net_worth = self.cash + cash_value_of_stock
        def adjust_cash_position(execution_price, buy_sell_indicator):
            if buy_sell_indicator == 'B':
                self.cash -= execution_price
            elif buy_sell_indicator == 'S':
                self.cash += execution_price
        event_as_kws = event.to_kwargs()
        execution_price = event.message.execution_price
        order_info =  self.orderstore.confirm('executed', **event_as_kws)
        buy_sell_indicator = order_info['buy_sell_indicator']
        price = order_info['price']
        order_token = event.message.order_token
        adjust_inventory(buy_sell_indicator)
        event.broadcast_msgs(
            'executed', order_token=order_token, price=price, 
            inventory=self.inventory.position, execution_price=execution_price,
            buy_sell_indicator=buy_sell_indicator, model=self)
        # orderstore delete order 
        # data after execution, hence
        # event carries order_info around
        # this way rest of the handlers in the chain 
        # can access order data
        event.attach(order_info=order_info)
        adjust_cash_position(execution_price, buy_sell_indicator)
        adjust_net_worth()


class InvestorFactory:
    @staticmethod
    def get_model(market):
        return ELOInvestor.from_otree_market(market)

class ELOInvestor(ELOTrader):
    model_name = 'inv'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.market_facts = {k: 0 for k in self.tracked_market_facts}

    @classmethod
    def from_otree_market(cls, market):
        args = (market.subsession_id, market.market_id, 1, market.id_in_subsession,
            'investor', market.exchange_host, market.exchange_port)  # one investor per market
        kwargs = {'token_prefix': 'INV'}
        return cls(*args, **kwargs)
        