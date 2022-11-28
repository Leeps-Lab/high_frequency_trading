# GoF - Design Patterns pg.291 - State

import logging
from .utility import (MIN_BID, MAX_ASK, elo_otree_player_converter)
from .market_elements.inventory import Inventory
from collections import namedtuple
from .equations import latent_bid_and_offer
from .market_elements.subscription import Subscription
from .orderstore import OrderStore
from .trader_state import TraderStateFactory, ELOOutState
import time

import logging

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

    def __init__(self, subsession_id, market_id, player_id, id_in_market,
            default_role, exchange_host, exchange_port, cash=0, 
            **kwargs):
        try:
            from .models import Player
            player = Player.objects.get(id=player_id)
            self.participant_code = player.participant.code
        except Player.DoesNotExist:
            self.participant_code = None
        self.subsession_id = subsession_id
        self.market_id = market_id
        self.id_in_market = id_in_market
        self.player_id = player_id
        self.exchange_host = exchange_host
        self.exchange_port = exchange_port
        self.orderstore = self.orderstore_cls(player_id, in_group_id=id_in_market, 
            **kwargs)
        self.account_id = kwargs.get('firm')
        self.tag = self.account_id or self.player_id
        self.inventory = Inventory()
        self.trader_role = TraderStateFactory.get_trader_state(default_role)
        self.market_facts = {k: None for k in self.tracked_market_facts}
        self.delayed = False
        self.staged_bid = None
        self.staged_offer = None
        self.implied_bid = None
        self.implied_offer = None
        self.disable_bid = False
        self.disable_offer = False
        self.midpoint_peg = False
        self.initial_endowment = cash
        self.cash = cash
        self.cost = 0
        self.net_worth = cash
        # an estimate of time of arrival for 
        # the most recent outbound message
        # I need this since delays can change arbitrarily
        # in a way that a later message can arrive
        # at the exchange earlier 
        # than a previous one
        self.default_delay = 0.5
        self.message_arrival_estimate = None 
        self.peg_price = None
        self.peg_state = None

        self.total_bids = 0
        self.total_asks = 0
        self.sum_bid_price = 0
        self.sum_ask_price = 0

        self.executed_price = None
        self.buy_sell_indicator = None
        
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
        log.info('trader %s: open session with market view: %s' % (self.tag,
                self.market_facts))
    
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
        self.trader_role.state_change(self,event)
            
        log.debug('trader %s: change trader role: %s' % (self.tag, trader_state))
        event.broadcast_msgs('role_confirm', role_name=new_state, model=self)

    @property
    def delay(self):
        """
        reads will trigger an update in message arrival estimate
        so that the next delay returned is after the previous one
        """
        # well, so this is really bad practice
        # but since the nature of this app 
        # I have to make assumptions around time..
        is_delayed_trader = self.delayed
        now = time.time()
        if not is_delayed_trader or self.message_arrival_estimate is None:
            self.message_arrival_estimate = now + self.default_delay
            delay = self.default_delay
        else:
            current_arrival_estimate = now + self.__delay
            if self.message_arrival_estimate > current_arrival_estimate:
                diff = self.message_arrival_estimate - current_arrival_estimate
                delay = diff + self.__delay
                self.message_arrival_estimate = now + delay 
            else:   
                self.message_arrival_estimate = current_arrival_estimate
                delay = self.__delay
        delay = round(delay, 4)
        log.debug('trader %s: message delay %s.' % (self.tag, delay))
        return delay

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
        'L': 'peg_state_change',
        'role_change': 'state_change', 
        'slider': 'user_slider_change'}
    otree_player_converter = elo_otree_player_converter


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.technology_subscription = Subscription(
            'speed_tech', self.player_id, kwargs.get('speed_unit_cost', 0))
        self.sliders = {'slider_a_x': 0, 'slider_a_y': 0, 'slider_a_z': 0}
        self.slider_multipliers = {
            'a_x': kwargs.get('a_x_multiplier', 1), 
            'a_y': kwargs.get('a_y_multiplier', 1)}
        self.tax_paid = 0
        self.speed_cost = 0
    
    def set_initial_strategy(self, slider_a_x, slider_a_y, slider_a_z, role, speed_on):
        k_a_x, k_a_y = self.slider_multipliers['a_x'], self.slider_multipliers['a_y']
        self.sliders = {
            'slider_a_x': slider_a_x * k_a_x , 'slider_a_y': slider_a_y * k_a_y,
            'slider_a_z': slider_a_z}
        self.trader_role = self.trader_state_factory.get_trader_state(role)
        self.delayed = speed_on
        if speed_on:
            self.delay = self.trader_role.short_delay
            self.technology_subscription.activate()
        else:
            self.delay = self.trader_role.long_delay
            self.technology_subscription.deactivate()
            speed_cost = self.technology_subscription.invoice()
            self.speed_cost += speed_cost
        
        self.executed_price = None
        self.buy_sell_indicator = None  

    def open_session(self, *args, **kwargs):
        super().open_session(*args, **kwargs)
        log.info(
# ok, this is quite ugly.. but useful..
'trader %s: parameters: a_x: %s, a_x multiplier: %s, a_y: %s, a_y multiplier: %s, \
w: %s, speed unit cost: %s' % (
    self.tag, self.sliders['slider_a_x'], self.slider_multipliers['a_x'],
    self.sliders['slider_a_y'], self.slider_multipliers['a_y'],
    self.sliders['slider_a_z'], self.technology_subscription.unit_cost))

    def close_session(self, event):
        inventory_value = self.inventory.valuate(self.market_facts['reference_price'])
        self.inventory.liquidify(
            self.market_facts['reference_price'], 
            discount_rate=self.market_facts['tax_rate'])
        #self.cash += self.inventory.cash
        tax_paid = self.inventory.cost
        if self.technology_subscription.is_active:
            self.technology_subscription.deactivate()
        speed_cost = self.technology_subscription.invoice()
        self.cost += tax_paid + speed_cost
        self.tax_paid += tax_paid
        self.speed_cost += speed_cost
        manual_net_worth =  self.initial_endowment + inventory_value + self.sum_ask_price - self.sum_bid_price  - self.cost
        #self.net_worth =  self.net_worth - self.cost + self.inventory.cash
        self.net_worth = manual_net_worth
        log.info('trader %s: speed_cost %s, tax_paid %s, net_worth %s' % (self.tag, speed_cost, tax_paid, self.net_worth))
        self.executed_price = None
        self.buy_sell_indicator = None  
    
    def user_slider_change(self, event):
        msg = event.message
        # a_z <-> w is always btw 0 - 1
        k_a_x, k_a_y = self.slider_multipliers['a_x'], self.slider_multipliers['a_y']
        self.sliders = {
            'slider_a_x': msg.a_x * k_a_x , 'slider_a_y': msg.a_y * k_a_y,
            'slider_a_z': msg.a_z}       
        event.broadcast_msgs('slider_confirm', a_x=self.sliders['slider_a_x'],
            a_y=self.sliders['slider_a_y'], a_z=self.sliders['slider_a_z'], model=self)       

        self.executed_price = None
        self.buy_sell_indicator = None  

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
        if not event.message.midpoint_peg:
            event_as_kws = event.to_kwargs()
            order_info = self.orderstore.confirm('enter', **event_as_kws)
            event.broadcast_msgs('confirmed', model=self, **event_as_kws)

            # if we're currently out, then this order is invalid and should be immediately canceled
            if isinstance(self.trader_role, ELOOutState):
                event.exchange_msgs('cancel', model=self, **order_info)
        
        self.executed_price = None
        self.buy_sell_indicator = None
    
    def order_replaced(self, event):
        event_as_kws = event.to_kwargs()
        order_info = self.orderstore.confirm('replaced', **event_as_kws)  
        order_token = event.message.replacement_order_token
        old_token = event.message.previous_order_token
        old_price = order_info['old_price']
        event.broadcast_msgs('replaced', order_token=order_token, 
            old_token=old_token, old_price=old_price, model=self, **event_as_kws)   

        self.executed_price = None
        self.buy_sell_indicator = None  

    def order_canceled(self, event):
        event_as_kws = event.to_kwargs()
        order_info = self.orderstore.confirm('canceled', **event_as_kws)
        order_token = event.message.order_token
        price = order_info['price']
        buy_sell_indicator = order_info['buy_sell_indicator']
        event.broadcast_msgs('canceled', order_token=order_token,
            price=price, buy_sell_indicator=buy_sell_indicator, 
            model=self)

        self.executed_price = None
        self.buy_sell_indicator = None

    def order_executed(self, event):
        def adjust_inventory(buy_sell_indicator):
            if buy_sell_indicator == 'B':
                self.total_bids += 1
                self.inventory.add()
            elif buy_sell_indicator == 'S':
                self.total_asks += 1
                self.inventory.remove()
        def adjust_net_worth():
            reference_price = self.market_facts['reference_price']
            cash_value_of_stock = self.inventory.valuate(reference_price)
            self.net_worth = self.cash + cash_value_of_stock
        def adjust_cash_position(execution_price, buy_sell_indicator):
            if buy_sell_indicator == 'B':
                self.sum_bid_price += execution_price
                self.cash -= execution_price
            elif buy_sell_indicator == 'S':
                self.sum_ask_price += execution_price
                self.cash += execution_price
        event_as_kws = event.to_kwargs()
        execution_price = event.message.execution_price
        order_info =  self.orderstore.confirm('executed', **event_as_kws)
        buy_sell_indicator = order_info['buy_sell_indicator']
        price = order_info['price']

        self.executed_price = execution_price
        self.buy_sell_indicator = buy_sell_indicator

        # Check to make sure reference_price isn't 0 for the first order in the market
        if self.market_facts['reference_price'] == 0:
            self.market_facts['reference_price'] = execution_price

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

    def peg_state_change(self, event):
        self.peg_price = event.message.peg_price
        # HACK: see exchange_server.exchange.iex_exchange.py:225
        if self.peg_price == -9999:
            self.peg_price = None
        self.peg_state = event.message.peg_state

        self.executed_price = None
        self.buy_sell_indicator = None  


class InvestorFactory:
    @staticmethod
    def get_model(market):
        return ELOInvestor.from_otree_market(market)

class ELOInvestor(ELOTrader):
    model_name = 'inv'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_delay = 0.01
        self.market_facts = {k: 0 for k in self.tracked_market_facts}

    @classmethod
    def from_otree_market(cls, market):
        args = (market.subsession_id, market.market_id, 1, market.id_in_subsession,
            'investor', market.exchange_host, market.exchange_port)  # one investor per market
        kwargs = {'firm': 'INVE'}
        return cls(*args, **kwargs)

    def order_accepted(self, event):
        super().order_accepted(event)
        self.midpoint_peg = event.message.midpoint_peg

    def order_replaced(self, event):
        super().order_replaced(event)
        self.midpoint_peg = event.message.midpoint_peg
        
    def order_canceled(self, event):
        super().order_canceled(event)
        self.midpoint_peg = event.message.midpoint_peg

    def order_executed(self, event):
        super().order_executed(event)
        self.midpoint_peg = event.message.midpoint_peg
    
