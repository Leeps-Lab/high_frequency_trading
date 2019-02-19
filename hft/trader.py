
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


class TraderFactory:
    
    def get_trader(self):
        raise NotImplementedError()

class ELOTraderFactory:
    @staticmethod
    def get_trader(role_name, subject_state):
        if role_name == 'maker_basic':
            return ELOBasicMaker(subject_state)
        elif role_name == 'out':
            return ELOOut(subject_state)
        elif role_name == 'maker_2':
            return ELONotSoBasicMaker(subject_state)
        elif role_name == 'taker':
            return ELOTaker(subject_state)
        else:
            raise Exception('unknown role: %s' % role_name)

class CDATraderFactory(TraderFactory):

    @staticmethod
    def get_trader(role_name, subject_state):
        if role_name == 'sniper':
            return BCSSniper(subject_state)
        elif role_name == 'maker':
            return BCSMaker(subject_state)
        elif role_name == 'out':
            return BCSOut(subject_state)
        else:
            raise Exception('unknown role: %s' % role_name)

class FBATraderFactory(TraderFactory):

    @staticmethod
    def get_trader(role_name, subject_state):
        if role_name == 'sniper':
            return BCSSniper(subject_state)
        elif role_name == 'maker':
            return BCSMaker(subject_state)
        elif role_name == 'out':
            return BCSOut(subject_state)
        else:
            log.warning('unknown role: %s' % role_name)

class BaseTrader:

    state_spec = None

    message_dispatch = {}

    def __init__(self, subject_state):
        for slot in subject_state.__slots__:
            setattr(self, slot, getattr(subject_state, slot))
        self.outgoing_messages = deque()

    def receive(self, event):
        if event.event_type not in self.message_dispatch:
            raise KeyError('Unknown message_type: %s for trader: %s' % (message_type,
                self.__class__.__name__) )
        handler_name = self.message_dispatch[event.event_type]
        handler = getattr(self, handler_name)
        self.event = event
        handler(**event.to_kwargs())
        self.event = None



    def first_move(self, **kwargs):
        """
        this gets called on a role 
        change
        override this
        """
        pass
        

class BCSTrader(BaseTrader):

    state_spec = BCSSubjectState

    short_delay = 0.1
    long_delay = 0.5

    message_dispatch = { 'spread_change': 'spread_change', 'speed_change': 'speed_change',
        'role_change': 'first_move', 'A': 'accepted', 'U': 'replaced', 'C': 'canceled', 
        'E': 'executed', 'fundamental_value_jumps': 'jump', 'slider_change': 'slider_change',
        'bbo_change': 'bbo_update', 'order_by_arrow': 'trader_bid_offer_change'}

    def speed_change(self, **kwargs):
        """
        switch between on speed, off speed
        record time if player turns on speed
        to use to calculate technology cost
        """
        self.speed_on = not self.speed_on
        if self.speed_on:
            # player subscribes to speed
            self.speed_on_start_time = nanoseconds_since_midnight()
        else:
            # player unsubscribes from speed
            time_on_speed = nanoseconds_since_midnight() - self.speed_on_start_time
            self.time_on_speed += time_on_speed
    
    def calc_delay(self) -> float:
        """
        returns the required time to delay an exchange message
        """
        delay = self.long_delay
        if self.speed_on is True:
            time_since_speed_change = nanoseconds_since_midnight() - self.speed_on_start_time 
            if time_since_speed_change < 5 * 1e6:
                # otherwise the order of messages may break
                return delay
            delay = self.short_delay
        return delay

    def update_cash_position(self, exec_price, buy_sell_indicator) -> int:
        raise NotImplementedError()

    def jump(self, **kwargs):
        """
        base trader's response to a jump event
        update fundamental price
        """
        new_fp = int(kwargs['new_fundamental'])
        is_positive = True if new_fp - self.fp > 0 else False
        self.fp = new_fp
        return is_positive
 
    def leave_market(self):
        """
        cancel all orders in market
        """
        orders = self.orderstore.all_orders()
        if orders:
            delay = self.calc_delay()
            host, port = self.exchange_host, self.exchange_port
            for order_info in orders:
                message_content = {'host': host, 'port': port, 
                    'type': 'cancel', 'delay': delay, 'order_info': order_info}
                internal_message = format_message('exchange', **message_content)
                self.outgoing_messages.append(internal_message)

    def accepted(self, **kwargs):
        self.orderstore.confirm('enter', **kwargs)
        order_token = kwargs['order_token']
        price = kwargs['price']
        buy_sell_indicator = kwargs['buy_sell_indicator']
        self.event.broadcast_messages('confirmed', order_token=order_token,
            price=price, buy_sell_indicator=buy_sell_indicator, 
            player_id=self.id, model=self)

    def replaced(self, **kwargs):
        order_info = self.orderstore.confirm('replaced', **kwargs)  
        order_token = kwargs['replacement_order_token']
        old_token = kwargs['previous_order_token']
        old_price = order_info['old_price']
        price = kwargs['price']
        buy_sell_indicator = kwargs['buy_sell_indicator']
        self.event.broadcast_messages('replaced', order_token=order_token,
            price=price, buy_sell_indicator=buy_sell_indicator, 
            old_token=old_token, old_price=old_price, player_id=self.id, model=self)

    def canceled(self, **kwargs):
        order_info = self.orderstore.confirm('canceled', **kwargs)
        order_token = kwargs['order_token']
        price = order_info['price']
        buy_sell_indicator = order_info['buy_sell_indicator']
        self.event.broadcast_messages('canceled', order_token=order_token,
            price=price, buy_sell_indicator=buy_sell_indicator, 
            player_id=self.id, model=self)

    def executed(self, **kwargs):
        execution_price = kwargs['execution_price']
        order_info =  self.orderstore.confirm('executed', **kwargs)
        buy_sell_indicator = order_info['buy_sell_indicator']
        self.update_cash_position(execution_price, buy_sell_indicator)
        price = order_info['price']
        order_token = kwargs['order_token']
        buy_sell_indicator = order_info['buy_sell_indicator']
        self.event.broadcast_messages('executed', order_token=order_token,
            price=price, inventory=self.orderstore.inventory, 
            buy_sell_indicator=buy_sell_indicator, player_id=self.id, model=self)
        return order_info

Sliders = namedtuple('Sliders', 'a_x a_y b_x b_y')
Sliders.__new__.__defaults__ = (0, 0, 0, 0)


class ELOTrader(BCSTrader):

    def update_cash_position(self, execution_price, buy_sell_indicator):
        if buy_sell_indicator == 'B':
            self.endowment -= execution_price
        elif buy_sell_indicator == 'S':
            self.endowment += execution_price

    def switch_to_market_tracking_role(self, **kwargs):
        self.best_quotes = {'B': kwargs['best_bid'], 'S': kwargs['best_offer']}
        self.best_quote_volumes = {'B': kwargs['volume_at_best_bid'], 
            'S': kwargs['volume_at_best_ask']}
        self.no_enter_until_bbo = {'B': False, 'S': False}
        self.order_imbalance = kwargs.get('order_imbalance')

    def exchange_message_from_order_info(self, order_info, delay, order_type):
        host, port = self.exchange_host, self.exchange_port
        message_content = {'host': host, 'port': port, 'type': order_type, 'delay':
            delay, 'order_info': order_info}
        exchange_message = format_message('exchange', **message_content)
        return exchange_message

    def first_move(self, **kwargs):
        self.role = kwargs['state']

class ELOOut(ELOTrader):

    def __init__(self, subject_state):
        super().__init__(subject_state)
    
    def first_move(self, **kwargs):
        super().first_move(**kwargs)
        self.leave_market()
        self.best_quotes['B'] = None
        self.best_quotes['S'] = None
        self.order_imbalance = None
        self.event.broadcast_messages('role_confirm', player_id=self.id, 
            role_name=self.role, market_id=self.market_id)
        

MIN_BID = 0
MAX_ASK = 2147483647

class ELOBasicMaker(ELOTrader):

    message_dispatch = { 'spread_change': 'spread_change', 'speed_change': 'speed_change',
        'role_change': 'first_move', 'A': 'accepted', 'U': 'replaced', 'C': 'canceled', 
        'E': 'executed', 'bbo_change': 'bbo_update', 'order_by_arrow': 'trader_bid_offer_change', 
        }

    def __init__(self, subject_state):
        super().__init__(subject_state)

    def first_move(self, **kwargs):
        super().first_move(**kwargs)
        self.leave_market()
        self.switch_to_market_tracking_role(**kwargs)
        self.event.broadcast_messages('role_confirm', player_id=self.id, 
            role_name=self.role, market_id=self.market_id)

    def trader_bid_offer_change(self, price=None, buy_sell_indicator=None, **kwargs):
        if buy_sell_indicator is None:
            buy_sell_indicator = kwargs['side']
        if price is None:
            price = price_grid(kwargs['price'])
        if price == MIN_BID or price == MAX_ASK:
            return
        else:
            orders = self.orderstore.all_orders(direction=buy_sell_indicator)
            delay = self.calc_delay()
            if orders:
                for o in orders:
                    existing_token = o['order_token']
                    existing_buy_sell_indicator = o['buy_sell_indicator']
                    if buy_sell_indicator == existing_buy_sell_indicator:
                        order_info = self.orderstore.register_replace(existing_token, price)
                        internal_message = self.exchange_message_from_order_info(order_info,
                            delay, 'replace')
                        self.outgoing_messages.append(internal_message)
            else:
                order_info = self.orderstore.enter(price=price, 
                    buy_sell_indicator=buy_sell_indicator, time_in_force=99999)
                internal_message = self.exchange_message_from_order_info(order_info,
                    delay, 'enter')
                self.outgoing_messages.append(internal_message)

    def bbo_update(self, **kwargs):
        self.best_quote_volumes['B'] = kwargs['volume_at_best_bid']
        self.best_quote_volumes['S'] = kwargs['volume_at_best_ask']
        self.best_quotes['B'] = kwargs['best_bid']
        self.best_quotes['S'] = kwargs['best_offer']

class ELONotSoBasicMaker(ELOTrader):

    message_dispatch = { 'spread_change': 'spread_change', 'speed_change': 'speed_change',
        'role_change': 'first_move', 'A': 'accepted', 'U': 'replaced', 'C': 'canceled', 
        'E': 'executed', 'slider': 'slider_change', 'bbo_change': 'latent_quote_update', 
        'order_imbalance_change': 'latent_quote_update'}

    def __init__(self, subject_state):
        super().__init__(subject_state)
    
    def first_move(self, **kwargs):
        super().first_move(**kwargs)
        self.leave_market()
        self.switch_to_market_tracking_role(**kwargs)
        self.sliders = Sliders()
        self.latent_quote = {'B': None, 'S': None}
        if self.best_quotes['B'] > MIN_BID:
            buy_message = self.enter_with_latent_quote('B')
            self.outgoing_messages.append(buy_message)
        if self.best_quotes['S'] < MAX_ASK:
            sell_message = self.enter_with_latent_quote('S')
            self.outgoing_messages.append(sell_message)
        self.event.broadcast_messages('role_confirm', player_id=self.id, 
            role_name=self.role, market_id=self.market_id)
    
    def enter_with_latent_quote(self, buy_sell_indicator, price=None, 
            time_in_force=99999, latent_quote_formula=latent_bid_and_offer):
        if price is None:
            latent_bid, latent_offer = latent_quote_formula(self.best_quotes['B'], 
                self.best_quotes['S'], self.order_imbalance, self.orderstore.inventory, 
                self.sliders)
            self.implied_quotes = {'B': latent_bid, 'S': latent_offer}
            price = latent_bid if buy_sell_indicator == 'B' else latent_offer
        delay = self.calc_delay()
        order_info = self.orderstore.enter(price=price, buy_sell_indicator=buy_sell_indicator, 
            time_in_force=time_in_force)
        exchange_message = self.exchange_message_from_order_info(order_info, 
            delay, 'enter')
        self.latent_quote[buy_sell_indicator] = price
        return exchange_message

    def slider_change(self, **kwargs):
        new_slider = Sliders(a_x=float(kwargs['a_x']), a_y=float(kwargs['a_y']))
        old_slider = self.sliders
        if old_slider != new_slider:
            self.latent_quote_update(sliders=new_slider)

    @staticmethod    
    def enter_rule(current_bid, current_offer, best_bid, best_offer, 
        implied_bid, implied_offer, volume_at_best_bid, volume_at_best_offer):
        bid = None
        if best_bid > MIN_BID and (current_bid != best_bid or 
            volume_at_best_bid > 1):
            if implied_bid != current_bid:
                bid = implied_bid

        offer = None      
        if  best_offer < MAX_ASK  and (current_offer != best_offer or
            volume_at_best_offer > 1):
            if implied_offer != current_offer:
                offer = implied_offer
        return (bid, offer)

    def latent_quote_update(self, latent_quote_formula=latent_bid_and_offer, sliders=None, **kwargs):
        if sliders is None:
            sliders = self.sliders
        else:
            self.sliders = sliders
        best_bid = kwargs.get('best_bid')
        if best_bid is None:
            best_bid = self.best_quotes['B']
        else:
            self.best_quotes['B'] = best_bid
            self.best_quote_volumes['B'] = kwargs['volume_at_best_bid']

        best_offer = kwargs.get('best_offer')
        if best_offer is None:
            best_offer = self.best_quotes['S']
        else:
            self.best_quotes['S'] = best_offer
            self.best_quote_volumes['S'] = kwargs['volume_at_best_ask']

        previous_order_imbalance = float(self.order_imbalance)
        current_order_imbalance = kwargs.get('order_imbalance')
        if current_order_imbalance is not None:
            self.order_imbalance = current_order_imbalance
        else:
            current_order_imbalance = previous_order_imbalance

        new_latent_bid, new_latent_offer = latent_quote_formula(best_bid, best_offer, 
            current_order_imbalance, self.orderstore.inventory, sliders)

        self.implied_quotes = {'B': new_latent_bid, 'S': new_latent_offer}   
        current_bid = self.latent_quote['B']
        current_offer = self.latent_quote['S']    

        volume_at_best_offer = self.best_quote_volumes['S']
        volume_at_best_bid = self.best_quote_volumes['B']


        bid, offer = self.enter_rule(current_bid, current_offer, best_bid, 
            best_offer, new_latent_bid, new_latent_offer, volume_at_best_bid, 
            volume_at_best_offer)

        start_from = 'B'
        if bid and offer:
            # start from the direction towards
            # the less aggressive price
            # in replaces.
            sell_is_aggressive = False
            if current_offer is not None and current_offer > offer:
                sell_is_aggressive = True
            buy_is_aggressive = False
            if current_bid is not None and current_bid < bid:
                buy_is_aggressive = True
            
            if buy_is_aggressive and not sell_is_aggressive:
                start_from = 'S'
        
        if bid or offer:
            order_imbalance = None
            if current_order_imbalance != previous_order_imbalance:
                order_imbalance = current_order_imbalance
            self.move_bid_and_offer(latent_bid=bid, latent_offer=offer, start_from=
                start_from, order_imbalance=order_imbalance)

    def move_bid_and_offer(self, latent_bid=None, latent_offer=None, start_from='B',
            order_imbalance=None):
        buys = deque()
        sells = deque()
        delay = self.calc_delay()
        
        if latent_offer is not None:
            sell_orders = self.orderstore.all_orders('S')
            assert len(sell_orders) <= 1, 'more than one sell order in market: %s' % self.orderstore
            if sell_orders:
                for o in sell_orders:
                    token = o['order_token']
                    order_price = o['price']
                    replace_price = o.get('replace_price', None)
                    if latent_offer != order_price and latent_offer != replace_price:
                        order_info = self.orderstore.register_replace(token, latent_offer)
                        sell_message = self.exchange_message_from_order_info(order_info, 
                        delay, 'replace')
                        sells.append(sell_message)
                self.latent_quote['S'] = latent_offer
            elif order_imbalance is None or self.no_enter_until_bbo['S'] is False:
                sell_message = self.enter_with_latent_quote('S', price=latent_offer)
                sells.append(sell_message)
                self.no_enter_until_bbo['S'] = False

        
        if latent_bid is not None:
            buy_orders = self.orderstore.all_orders('B')
            assert len(buy_orders) <= 1, 'more than one buy order in market: %s' % self.orderstore
            if buy_orders:
                for o in buy_orders:
                    token = o['order_token']
                    order_price = o['price']
                    replace_price = o.get('replace_price', None)
                    if latent_bid != order_price and latent_bid != replace_price:
                        order_info = self.orderstore.register_replace(token, latent_bid)
                        buy_message = self.exchange_message_from_order_info(order_info, 
                            delay, 'replace')
                        buys.append(buy_message)
                self.latent_quote['B'] = latent_bid
            elif order_imbalance is None or self.no_enter_until_bbo['B'] is False:
                    buy_message = self.enter_with_latent_quote('B', price=latent_bid)
                    buys.append(buy_message)
                    self.no_enter_until_bbo['B'] = False

        
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

        latent_bid = self.latent_quote['B']
        if  buy_sell_indicator == 'B' and latent_bid == price:
            self.latent_quote['B'] = None
        
        latent_offer = self.latent_quote['S']
        if  buy_sell_indicator == 'S' and latent_offer == price:
            self.latent_quote['S'] = None

        if (self.best_quote_volumes[buy_sell_indicator] == 1 and 
            self.best_quotes[buy_sell_indicator] == price):
            self.no_enter_until_bbo[buy_sell_indicator] = True


class ELOTaker(ELONotSoBasicMaker):

    def first_move(self, **kwargs):
        self.role = kwargs['state']
        self.leave_market()
        self.switch_to_market_tracking_role(**kwargs)
        self.sliders = Sliders()
        self.latent_quote = {'B': None, 'S': None}
        self.event.broadcast_messages('role_confirm', player_id=self.id, 
            role_name=self.role, market_id=self.market_id)
    
    @staticmethod    
    def enter_rule(current_bid, current_offer, best_bid, best_offer, 
        implied_bid, implied_offer, volume_at_best_bid, volume_at_best_offer):
        bid = None
        if best_bid > MIN_BID and implied_bid > best_bid:
            if implied_bid != current_bid:
                bid = implied_bid

        offer = None      
        if  best_offer < MAX_ASK  and implied_offer < best_offer:
            if implied_offer != current_offer:
                offer = implied_offer
        return (bid, offer)


    def move_bid_and_offer(self, latent_bid=None, latent_offer=None, start_from='B',
            order_imbalance=None):
        messages = deque()
        
        if latent_offer is not None:
            sell_message = self.enter_with_latent_quote('S', price=latent_offer,
                time_in_force=0)
            messages.append(sell_message)
       
        if latent_bid is not None:
            buy_message = self.enter_with_latent_quote('B', price=latent_bid,
                time_in_force=0)
            messages.append(buy_message)

        self.outgoing_messages.extend(messages)