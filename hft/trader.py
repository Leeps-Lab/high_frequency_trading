
import math
import logging
from .utility import (nanoseconds_since_midnight, ouch_fields, format_message,
    MIN_BID, MAX_ASK)

from collections import deque
from . import translator as translate
from .subject_state import *
from collections import namedtuple
from .equations import latent_bid_and_offer, price_grid
log = logging.getLogger(__name__)

import time

# this module will be updated soon.

class TraderFactory:
    @staticmethod
    def get_trader(market_environment, role_name, subject_state):
        if role_name == 'manual':
            return ELOManualTrader(subject_state)
        elif role_name == 'out':
            return ELOOut(subject_state)
        elif role_name == 'automated':
            return ELOAutomatedTrader(subject_state)
        else:
            raise Exception('unknown role: %s' % role_name)

class BaseTrader(object):

    state_spec = None
    model_name = 'trader'
    message_dispatch = {}

    def __init__(self, subject_state):
        for slot in subject_state.__slots__:
            setattr(self, slot, getattr(subject_state, slot))
        self.outgoing_messages = deque()

    def receive(self, event):
        if event.event_type not in self.message_dispatch:
            log.debug('Unknown message_type: %s for trader: %s' % (event.event_type,
                self.__class__.__name__) )
            return
        handler_name = self.message_dispatch[event.event_type]
        handler = getattr(self, handler_name)
        self.event = event
        handler(**event.to_kwargs())
        self.event = None

    def market_start(self, **kwargs):
        for k, v in kwargs:
            if hasattr(self, k):
                setattr(self, k, v)


    def first_move(self, **kwargs):
        """
        this gets called on a role 
        change
        override this
        """
        pass
    

class ELOTrader(BaseTrader):
    state_spec = ELOSubjectState

    short_delay = 0.1
    long_delay = 0.5

    message_dispatch = { 'speed_change': 'speed_change',
        'role_change': 'first_move', 'A': 'accepted', 'U': 'replaced', 'C': 'canceled', 
        'E': 'executed', 'slider': 'slider_change', 'bbo_change': 'bbo_change', 
        'order_imbalance_change': 'order_imbalance_change', 'market_end': 'close_session',
        'market_start': 'market_start', 'reference_price_change': 'reference_price_update',
        'signed_volume_change': 'signed_volume_change', 'external_feed_change': 'external_feed_update'}
    
    cost_fields = ('technology_cost', 'tax')

    @property
    def delay(self):
        delay = self.long_delay
        if self.speed_on is True:
            time_since_speed_change = time.time() - self.speed_on_start_time 
            if time_since_speed_change < delay:
                # so this order doesn't beat the previous
                return delay
            delay = self.short_delay
        return delay

    def open_session(self, **kwargs):
        for field in ('best_bid', 'volume_at_best_bid', 'next_bid', 'best_offer',
            'volume_at_best_offer', 'next_offer', 'signed_volume', 'e_best_bid',
            'e_best_offer', 'e_signed_volume','tax_rate'):
                setattr(self, field, kwargs[field])

    def speed_change(self, **kwargs):
        new_state = kwargs['value']
        if new_state == self.speed_on:
            return
        self.speed_on = new_state
        now = time.time()
        if self.speed_on:
            # if subscribe
            self.speed_on_start_time = now
        else:
            duration = now - self.speed_on_start_time
            self.time_on_speed += duration
            tech_cost_step = self.technology_unit_cost * duration
            self.technology_cost += tech_cost_step
        self.event.broadcast_msgs(
            'speed_confirm', value=self.speed_on, player_id=self.player_id, 
            market_id=self.market_id)

    def close_session(self, **kwargs):
        tax_rate = kwargs['tax_rate']
        reference_price = kwargs['reference_price']
        self.tax = abs(tax_rate * (reference_price * self.orderstore.inventory))
        self.cash += reference_price * self.orderstore.inventory
        self.speed_change(value=False)
        for field in self.cost_fields:
            if hasattr(self, field):
                trade_cost = getattr(self, field)
                try:
                    self.cost += trade_cost
                except:
                    log.exception('failed to add cost: {}'.format(trade_cost))
        self.wealth = self.cash - self.cost

    def leave_market(self):
        """
        cancel all orders in market
        """
        orders = self.orderstore.all_orders()
        if orders:
            delay = self.delay
            host, port = self.exchange_host, self.exchange_port
            for order_info in orders:
                order_info['shares'] = 0    # cancel fully
                message_content = {'host': host, 'port': port, 
                    'type': 'cancel', 'delay': delay, 'order_info': order_info}
                internal_message = format_message('exchange', **message_content)
                self.outgoing_messages.append(internal_message)

    def first_move(self, **kwargs):
        self.role = kwargs['state']
        self.speed_change(value=False)
        self.leave_market()
        self.wait_for_best_bid = False
        self.wait_for_best_offer = False
        self.event.broadcast_msgs(
            'role_confirm', role_name=self.role, model=self)

    def accepted(self, **kwargs):
        self.orderstore.confirm('enter', **kwargs)
        self.event.broadcast_msgs(
            'confirmed', model=self, **kwargs)

    def replaced(self, **kwargs):
        order_info = self.orderstore.confirm('replaced', **kwargs)  
        order_token = kwargs['replacement_order_token']
        old_token = kwargs['previous_order_token']
        old_price = order_info['old_price']
        self.event.broadcast_msgs(
            'replaced', order_token=order_token, old_token=old_token, 
            old_price=old_price, model=self, **kwargs)

    def canceled(self, **kwargs):
        order_info = self.orderstore.confirm('canceled', **kwargs)
        order_token = kwargs['order_token']
        price = order_info['price']
        buy_sell_indicator = order_info['buy_sell_indicator']
        self.event.broadcast_msgs('canceled', order_token=order_token,
            price=price, buy_sell_indicator=buy_sell_indicator, 
            model=self)

    def executed(self, **kwargs):
        execution_price = kwargs['execution_price']
        order_info =  self.orderstore.confirm('executed', **kwargs)
        buy_sell_indicator = order_info['buy_sell_indicator']
        self.post_execution(buy_sell_indicator=buy_sell_indicator, **kwargs)
        price = order_info['price']
        order_token = kwargs['order_token']
        self.event.broadcast_msgs('executed', order_token=order_token,
            price=price, inventory=self.orderstore.inventory, execution_price=execution_price,
            buy_sell_indicator=buy_sell_indicator, model=self)
        return order_info

    def post_execution(self, **kwargs):
        buy_sell_indicator = kwargs['buy_sell_indicator']
        execution_price = kwargs['execution_price']
        if buy_sell_indicator == 'B':
            self.cash -= execution_price
        elif buy_sell_indicator == 'S':
            self.cash += execution_price

    def exchange_message_from_order_info(self, order_info, delay, order_type):
        message_content = {'host': self.exchange_host, 'port': self.exchange_port, 
            'type': order_type, 'delay': delay, 'order_info': order_info}
        exchange_message = format_message('exchange', **message_content)
        return exchange_message

    def bbo_change(self, **kwargs):
        for field in ('best_bid', 'volume_at_best_bid', 'next_bid', 'best_offer',
            'volume_at_best_offer', 'next_offer'):
                setattr(self, field, kwargs[field])

    def reference_price_update(self, **kwargs):
        self.reference_price = kwargs['reference_price']

    def external_feed_update(self, **kwargs):
        for k in ('e_best_bid','e_best_offer', 'e_signed_volume'):
            setattr(self, k, kwargs[k])
        
    def signed_volume_change(self, **kwargs):
        if self.signed_volume != kwargs['signed_volume']:
            self.signed_volume = kwargs['signed_volume']


Sliders = namedtuple('Sliders', 'a_x a_y a_z')
Sliders.__new__.__defaults__ = (0, 0, 0)


# class ELOTrader(BCSTrader):

    # def post_execution(self, **kwargs):
    #     buy_sell_indicator = kwargs['buy_sell_indicator']
    #     execution_price = kwargs['execution_price']
    #     if buy_sell_indicator == 'B':
    #         self.cash -= execution_price
    #     elif buy_sell_indicator == 'S':
    #         self.cash += execution_price

    # def track_market(self, **kwargs):
        # self.best_bid = kwargs['best_bid']
        # self.best_offer = kwargs['best_offer']
        # self.volume_at_best_bid = kwargs['volume_at_best_bid']
        # self.volume_at_best_offer = kwargs['volume_at_best_offer']
        # self.wait_for_best_bid = False
        # self.wait_for_best_offer = False
        # self.order_imbalance = kwargs['order_imbalance']
    
    # def close_session(self, **kwargs):
    #     # tax_rate = kwargs['tax_rate']
    #     # reference_price = kwargs['reference_price']
    #     # self.tax = abs(tax_rate * (reference_price * self.orderstore.inventory))
    #     # self.cash += reference_price * self.orderstore.inventory
    #     super().close_session()

    # def exchange_message_from_order_info(self, order_info, delay, order_type):
    #     message_content = {'host': self.exchange_host, 'port': self.exchange_port, 
    #         'type': order_type, 'delay': delay, 'order_info': order_info}
    #     exchange_message = format_message('exchange', **message_content)
    #     return exchange_message

    # def first_move(self, **kwargs):
    #     self.role = kwargs['state']
    #     self.speed_change(value=False)
    
    # def reference_price_update(self, **kwargs):
    #     self.reference_price = kwargs['reference_price']

    # def bbo_update(self, **kwargs):
    #     for field in ('best_bid', 'volume_at_best_bid', 'next_bid', 'best_offer',
    #         'volume_at_best_offer', 'next_offer'):
    #             setattr(self, field, kwargs[field])


class ELOOut(ELOTrader):
    pass

#     def __init__(self, subject_state):
#         super().__init__(subject_state)
    
    # def first_move(self, **kwargs):
    #     super().first_move(**kwargs)
    #     self.leave_market()
        # self.track_market(**kwargs)
        # self.event.broadcast_messages('role_confirm', player_id=self.id, 
        #     role_name=self.role, market_id=self.market_id)
    
    # def bbo_update(self, **kwargs):
    #     self.volume_at_best_bid = kwargs['volume_at_best_bid']
    #     self.volume_at_best_offer = kwargs['volume_at_best_ask']
    #     self.best_bid = kwargs['best_bid']
    #     self.best_offer = kwargs['best_offer']
        

MIN_BID = 0
MAX_ASK = 2147483647

class ELOManualTrader(ELOTrader):

    message_dispatch = {
        'speed_change': 'speed_change', 'role_change': 'first_move', 'A': 'accepted', 
        'U': 'replaced', 'C': 'canceled', 'E': 'executed', 'bbo_change': 'bbo_change', 
        'order_entered': 'user_order', 'market_end': 'close_session', 
        'reference_price_change': 'reference_price_update'}

    # def __init__(self, subject_state):
    #     super().__init__(subject_state)

    # def first_move(self, **kwargs):
    #     super().first_move(**kwargs)
    #     self.leave_market()
    #     # self.track_market(**kwargs)
    #     self.event.broadcast_messages('role_confirm', player_id=self.id, 
    #         role_name=self.role, market_id=self.market_id)

    def user_order(self, **kwargs):
        # if buy_sell_indicator is None:
        #     buy_sell_indicator = kwargs['buy_sell_indicator']
        # if price is None:
        #     price = kwargs['price']
        buy_sell_indicator = kwargs['buy_sell_indicator']
        price = kwargs['price']
        if price == MIN_BID or price == MAX_ASK :
            return
        if (buy_sell_indicator == 'B' and self.target_offer is not None and 
            price >= self.target_offer) or (
            buy_sell_indicator == 'S' and self.target_bid is not None and 
            price <= self.target_bid):
            return
        else:
            orders = self.orderstore.all_orders(direction=buy_sell_indicator)
            if orders:
                for o in orders:
                    existing_token = o['order_token']
                    existing_buy_sell_indicator = o['buy_sell_indicator']
                    if buy_sell_indicator == existing_buy_sell_indicator:
                        order_info = self.orderstore.register_replace(existing_token, price)
                        internal_message = self.exchange_message_from_order_info(order_info,
                            self.delay, 'replace')
                        self.outgoing_messages.append(internal_message)
            else:
                order_info = self.orderstore.enter(price=price, 
                    buy_sell_indicator=buy_sell_indicator, time_in_force=99999)
                internal_message = self.exchange_message_from_order_info(order_info,
                    self.delay, 'enter')
                self.outgoing_messages.append(internal_message)
            if buy_sell_indicator == 'B':
                self.target_bid = price
            elif buy_sell_indicator == 'S':
                self.target_offer = price

    def executed(self, **kwargs):
        order_info = super().executed(**kwargs)
        price = order_info['price']          
        buy_sell_indicator = order_info['buy_sell_indicator']

        if  buy_sell_indicator == 'B' and self.target_bid == price:
            self.target_bid = None
        
        if  buy_sell_indicator == 'S' and self.target_offer == price:
            self.target_offer = None

    # def bbo_update(self, **kwargs):
    #     self.volume_at_best_bid = kwargs['volume_at_best_bid']
    #     self.volume_at_best_offer = kwargs['volume_at_best_ask']
    #     self.best_bid = kwargs['best_bid']
    #     self.best_offer = kwargs['best_offer']
    #     self.next_bid = kwargs['next_bid']
    #     self.next_offer = kwargs['next_offer']

class ELOAutomatedTrader(ELOTrader):

    # def __init__(self, subject_state):
    #     super().__init__(subject_state)
    
    def first_move(self, **kwargs):
        super().first_move(**kwargs)
        # self.leave_market()
        # self.track_market(**kwargs)
        self.sliders = Sliders()
        if self.best_bid > MIN_BID:
            buy_message = self.enter_with_latent_quote('B')
            self.outgoing_messages.append(buy_message)
        if self.best_offer < MAX_ASK:
            sell_message = self.enter_with_latent_quote('S')
            self.outgoing_messages.append(sell_message)

    def enter_with_latent_quote(self, buy_sell_indicator, price=None, 
            time_in_force=99999, latent_quote_formula=latent_bid_and_offer):
        if price is None:
            self.implied_bid, self.implied_offer = latent_quote_formula(self.best_bid, 
                self.best_offer, self.order_imbalance, self.orderstore.inventory, 
                self.sliders)
            price = self.implied_bid if buy_sell_indicator == 'B' else self.implied_offer 
        # delay = self.calc_delay()
        order_info = self.orderstore.enter(price=price, buy_sell_indicator=buy_sell_indicator, 
            time_in_force=time_in_force)
        exchange_message = self.exchange_message_from_order_info(order_info, 
            self.delay, 'enter')
        if buy_sell_indicator == 'B':
            self.target_bid = price
        elif buy_sell_indicator == 'S':
            self.target_offer = price
        return exchange_message
    
    def bbo_change(self, **kwargs):
        # for field in ('best_bid', 'volume_at_best_bid', 'next_bid', 'best_offer',
        #     'volume_at_best_offer', 'next_offer'):
        #     if field in kwargs:
        #         setattr(self, field, kwargs[field])
        super().bbo_update(**kwargs)
        self.wait_for_best_bid = False
        self.wait_for_best_offer = False
        self.latent_quote_update(**kwargs)
    
    def external_feed_change(self, **kwargs):
        super().external_feed_change(**kwargs)
        self.latent_quote_update(**kwargs)

    def signed_volume_change(self, **kwargs):
        buy_sell_indicator = kwargs['buy_sell_indicator']
        if self.signed_volume != kwargs['signed_volume']:
            self.signed_volume = kwargs['signed_volume']
            # wait if I am at the bbo because it might change
            # what if I am not alone ??
            if (buy_sell_indicator == 'B' and self.best_bid == self.target_bid):
                self.wait_for_best_bid = True
            if (buy_sell_indicator == 'S' and self.best_offer == self.target_offer):
                self.wait_for_best_offer = True
            self.latent_quote_update(**kwargs)

    def slider_change(self, **kwargs):
        new_slider = Sliders(
            a_x=float(kwargs['a_x']), a_y=float(kwargs['a_y'], a_z=float(kwargs['a_z'])))
        if self.sliders != new_slider:
            self.sliders = new_slider
            self.latent_quote_update(sliders=new_slider)
    
    @staticmethod    
    def enter_rule(current_bid, current_offer, best_bid_except_me, best_offer_except_me, 
        best_bid, best_offer, implied_bid, implied_offer, volume_at_best_bid, volume_at_best_offer,
        ticksize=10000):
        bid = None
        offer = None

        if best_bid_except_me > MIN_BID:
            if implied_bid != current_bid:
                bid = implied_bid
                # if implied_offer and implied_bid >= implied_offer:
                #     bid = implied_offer - ticksize
                # elif not implied_offer and current_offer and implied_bid > current_offer:
                #         bid = current_offer - ticksize
                # else:
                #     bid = implied_bid
                # if bid >= best_offer:
                #     bid = best_offer - ticksize

        if best_offer_except_me < MAX_ASK:
            if implied_offer != current_offer:
                offer = implied_offer
                # if implied_bid and implied_offer <= implied_bid:
                #     offer = implied_bid + ticksize
                # elif not implied_bid and current_bid and implied_offer < current_bid:
                #     offer = current_bid + ticksize
                # else:
                #     offer = implied_offer
                # if offer <= best_bid:
                #     offer = best_bid + ticksize
        return (bid, offer)

    @property
    def best_bid_except_me(self):
        if self.best_bid == self.target_bid and self.volume_at_best_bid == 1:
            return self.next_bid
        else:
            return self.best_bid

    @property
    def best_offer_except_me(self):
        if self.best_offer == self.target_offer and self.volume_at_best_offer == 1:
            return self.next_offer
        else:
            return self.best_offer

    def latent_quote_update(self, latent_quote_formula=latent_bid_and_offer, sliders=None, **kwargs):
        # best_bid_except_me = self.best_bid
        # best_offer_except_me = self.best_offer
        # if self.best_bid == self.target_bid and self.volume_at_best_bid == 1:
        #     best_bid_except_me = self.next_bid
        # if self.best_offer == self.target_offer and self.volume_at_best_offer == 1:
        #     best_offer_except_me = self.next_offer

        self.implied_bid, self.implied_offer = latent_quote_formula(
            self.best_bid_except_me, self.best_offer_except_me, self.signed_volume, 
            self.e_best_bid, self.e_best_offer, self.e_signed_volume,
            self.orderstore.inventory, self.sliders)

        bid, offer = self.enter_rule(self.target_bid, self.target_offer, self.best_bid_except_me, 
            self.best_offer_except_me, self.best_bid, self.best_offer, self.implied_bid, 
            self.implied_offer, self.volume_at_best_bid, self.volume_at_best_offer)

        start_from = 'B'
        if bid and offer:
            # start from the direction towards
            # the less aggressive price
            # in replaces.
            sell_is_aggressive = False
            if self.target_offer is not None and self.target_offer > offer:
                sell_is_aggressive = True
            buy_is_aggressive = False
            if self.target_bid is not None and self.target_bid < bid:
                buy_is_aggressive = True
            
            if buy_is_aggressive and not sell_is_aggressive:
                start_from = 'S'
        
        if bid or offer:
            self.move_bid_and_offer(target_bid=bid, target_offer=offer, start_from=
                start_from)

    def move_bid_and_offer(self, target_bid=None, target_offer=None, start_from='B'):
        delay = self.calc_delay()

        sells = deque()
        if target_offer is not None and self.wait_for_best_offer is False:
            sell_orders = self.orderstore.all_orders('S')
            if len(sell_orders) > 1:
                log.warning('multiple sell orders in market: %s:%s' % (self.orderstore, sell_orders))
            if sell_orders:
                for o in sell_orders:
                    token = o['order_token']
                    order_price = o['price']
                    replace_price = o.get('replace_price', None)
                    if target_offer != order_price and target_offer != replace_price:
                        order_info = self.orderstore.register_replace(token, target_offer)
                        sell_message = self.exchange_message_from_order_info(order_info, 
                            delay, 'replace')
                        sells.append(sell_message)
                self.target_offer = target_offer
            else:
                sell_message = self.enter_with_latent_quote('S', price=target_offer)
                sells.append(sell_message)

        buys = deque()
        if target_bid is not None and self.wait_for_best_bid is False:
            buy_orders = self.orderstore.all_orders('B')
            if len(buy_orders) > 1:
                log.warning('multiple buy orders in market: %s:%s' % (self.orderstore, buy_orders))
            if buy_orders:
                for o in buy_orders:
                    token = o['order_token']
                    order_price = o['price']
                    replace_price = o.get('replace_price', None)
                    if target_bid != order_price and target_bid != replace_price:
                        order_info = self.orderstore.register_replace(token, target_bid)
                        buy_message = self.exchange_message_from_order_info(order_info, 
                            delay, 'replace')
                        buys.append(buy_message)
                self.target_bid = target_bid
            else:
                buy_message = self.enter_with_latent_quote('B', price=target_bid)
                buys.append(buy_message)

        if start_from == 'B':
            self.outgoing_messages.extend(buys)
            self.outgoing_messages.extend(sells)
        else:
            self.outgoing_messages.extend(sells)
            self.outgoing_messages.extend(buys)

    def executed(self, **kwargs):
        order_info = super().executed(**kwargs)
        price = order_info['price']          
        buy_sell_indicator = order_info['buy_sell_indicator']

        if  buy_sell_indicator == 'B' and self.target_bid == price:
            self.target_bid = None
        
        if  buy_sell_indicator == 'S' and self.target_offer == price:
            self.target_offer = None

        if buy_sell_indicator == 'B':
            if self.best_bid == 1 and self.best_bid == price:
                self.wait_for_best_bid = True

        if buy_sell_indicator == 'S':
            if self.best_offer == 1 and self.best_offer == price:
                self.wait_for_best_offer = True


# class ELOTaker(ELOMaker):

#     def first_move(self, **kwargs):
#         # self.role = kwargs['state']
#         # self.speed_change(value=False)
#         # self.leave_market()
#         # self.track_market(**kwargs)
#         self.sliders = Sliders()
#         # self.event.broadcast_messages('role_confirm', player_id=self.id, 
#         #     role_name=self.role, market_id=self.market_id)
    
#     @staticmethod    
#     def enter_rule(current_bid, current_offer, best_bid_except_me, best_offer_except_me, 
#         best_bid, best_offer, implied_bid, implied_offer, volume_at_best_bid, volume_at_best_offer):
#         bid = None
#         if best_bid > MIN_BID and implied_bid > best_offer:
#             bid = implied_bid

#         offer = None      
#         if  best_offer < MAX_ASK  and implied_offer < best_bid:
#             offer = implied_offer
#         return (bid, offer)

#     def latent_quote_update(self, *args, **kwargs):
#         super().latent_quote_update(*args, **kwargs)
#         self.event.broadcast_messages('elo_quote_cue', player_id=self.id,
#             market_id=self.market_id, bid=self.implied_bid, offer=self.implied_offer)

#     def move_bid_and_offer(self, target_bid=None, target_offer=None, start_from='B',
#             order_imbalance=None):
#         messages = deque()
        
#         if target_offer is not None:
#             sell_message = self.enter_with_latent_quote('S', price=target_offer,
#                 time_in_force=0)
#             messages.append(sell_message)
       
#         if target_bid is not None:
#             buy_message = self.enter_with_latent_quote('B', price=target_bid,
#                 time_in_force=0)
#             messages.append(buy_message)

#         self.outgoing_messages.extend(messages)