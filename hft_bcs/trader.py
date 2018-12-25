
import math
import logging
from . import client_messages
from .utility import nanoseconds_since_midnight, ouch_fields, format_message


from collections import deque
from . import translator as translate
from .subject_state import *
from .hft_logging.experiment_log import *
from .hft_logging.session_events import log_events
from .hft_logging import row_formatters as hfl

from collections import namedtuple
from .equations import latent_bid_and_offer, price_grid
log = logging.getLogger(__name__)


class TraderFactory:
    
    def get_trader(self):
        raise NotImplementedError()

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
            log.warning('unknown role: %s' % role_name)

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

    def receive(self, message_type, **kwargs) -> dict:
        """
        assumes arguments include key event_source
        """
        lookup_key = message_type
        handler_name = self.message_dispatch[lookup_key]
        handler = getattr(self, handler_name)
        handler(**kwargs)


    def first_move(self, **kwargs):
        """
        this gets called on a role 
        change by player model
        it is a good idea to override this
        """
        pass
        

class BCSTrader(BaseTrader):

    state_spec = BCSSubjectState

    short_delay = 0.1
    long_delay = 0.5

    message_dispatch = { 'spread_change': 'spread_change', 'speed_change': 'speed_change',
        'role_change': 'first_move', 'A': 'accepted', 'U': 'replaced', 'C': 'canceled', 
        'E': 'executed', 'fundamental_value_jumps': 'jump', 'slider_change': 'slider_change',
        'bbo_change': 'bbo_update'}

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
        delay = 0.5
        if self.speed_on is True:
            time_since_speed_change = nanoseconds_since_midnight() - self.speed_on_start_time 
            if time_since_speed_change < 5 * 1e6:
                # otherwise the order of messages may break
                return delay
            delay = 0.1
        return delay

    def profit(self, exec_price, buy_sell_indicator) -> int:
        fp = self.fp
        d = abs(fp - exec_price)
        if exec_price < fp:
            # buyer (seller) buys (sells) less than fp
            profit = d if buy_sell_indicator == 'B' else -d  
        else:
            # seller (buyer) sells (buys) higher than fp
            profit = d if buy_sell_indicator == 'S' else -d  
        return profit

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

    def replaced(self, **kwargs):
        self.orderstore.confirm('replaced', **kwargs)  
     
    def canceled(self, **kwargs):
        self.orderstore.confirm('canceled', **kwargs)
        order_token = kwargs['order_token']
        message_content = {'group_id': self.market, 'type': 'canceled', 'message': {
            'id': self.id_in_group, 'order_token': order_token }
            }
        internal_message = format_message('broadcast', **message_content)
        self.outgoing_messages.append(internal_message)
    
    def executed(self, **kwargs):
        order_info =  self.orderstore.confirm('executed', **kwargs)
        exec_price, side = kwargs['execution_price'], order_info['buy_sell_indicator']
        order_token = kwargs['order_token']
        profit = self.profit(exec_price, side)
        self.endowment += profit
        message_content = { 'group_id': self.market, 'type': 'executed', 'message': {
            'profit': profit, 'execution_price': exec_price, 'order_token': order_token,
            'id': self.id_in_group }
            }
        internal_message = format_message('broadcast', **message_content)
        self.outgoing_messages.append(internal_message)
        return order_info
            
            
class BCSMaker(BCSTrader):

    def calc_price(self, buy_sell_indicator):
        """
        return order price for a maker order based on spread
        """
        leg_length = int(self.spread / 2)
        multiplier = -1 if buy_sell_indicator == 'B' else 1
        price = int(self.fp + multiplier * leg_length)
        return price

    def first_move(self, **kwargs):
        delay = self.calc_delay()
        for side in ('B', 'S'):
            price = self.calc_price(side)
            order_info = self.orderstore.enter(price=price, buy_sell_indicator=side, 
                            time_in_force=99999)
            host, port = self.exchange_host, self.exchange_port
            message_content = {'host': host, 'port': port, 'type': 'enter', 'delay':
                delay, 'order_info': order_info}
            internal_message = format_message('exchange', **message_content)
            self.outgoing_messages.append(internal_message)

    def jump(self, **kwargs):
        """
        assumes trader has active/pending orders in market
        reprice orders
        replace sell order first if jump is positive
        """
        is_positive_jump = super().jump(**kwargs)
        # get list of active or pending orders
        self.makers_reprice(start_from_above=is_positive_jump)

    def makers_reprice(self, start_from_above=True):
        orders = self.orderstore.all_orders()
        assert len(orders) <= 2, 'more than two orders in market: %s' % self.orderstore
        sorted_orders = sorted(orders, key=lambda order: order['price'], 
                            reverse=start_from_above)
        delay = self.calc_delay()
        for o in sorted_orders:
            token, buy_sell_indicator = o['order_token'], o['buy_sell_indicator']
            new_price = self.calc_price(buy_sell_indicator)
            order_info = self.orderstore.register_replace(token, new_price)
            host, port = self.exchange_host, self.exchange_port
            message_content = {'host': host, 'port': port, 'type': 'replace', 'delay':
                delay, 'order_info': order_info}
            internal_message = format_message('exchange', **message_content)
            self.outgoing_messages.append(internal_message)

    def spread_change(self, **kwargs):
        new_spread = int(kwargs['spread'])
        self.spread = new_spread
        self.makers_reprice()

        
    def maker_broadcast_info(self, order_token):
        low_leg, high_leg = int(self.fp - self.spread / 2), int(self.fp + self.spread / 2)
        message_content = { 'group_id': self.market, 'type': 'maker_confirm', 
            'message': { 'leg_up': high_leg, 'leg_down': low_leg, 'order_token': order_token, 
                'id': self.id_in_group }}
        internal_message = format_message('broadcast', **message_content)     
        return internal_message

    def accepted(self, **kwargs):
        super().accepted(**kwargs)
        order_token = kwargs['order_token']
        broadcast_info = self.maker_broadcast_info(order_token)
        self.outgoing_messages.append(broadcast_info)

    def replaced(self, **kwargs):
        super().replaced(**kwargs)  
        order_token = kwargs['replacement_order_token']
        broadcast_info = self.maker_broadcast_info(order_token)
        self.outgoing_messages.append(broadcast_info)

    def executed(self, **kwargs):
        order_info = super().executed(**kwargs)
        time_in_force = order_info['time_in_force']
        side = order_info['buy_sell_indicator']
        # make sure it is not a sniper order.
        if time_in_force != 0:
            host, port = self.exchange_host, self.exchange_port
            price = self.calc_price(side)
            delay = self.calc_delay()
            order_info = self.orderstore.enter(price=price, buy_sell_indicator=side, 
                            time_in_force=99999)
            message_content = {'host': host, 'port': port, 'type': 'enter', 'delay':
                delay, 'order_info': order_info}
            internal_message = format_message('exchange', **message_content)
            self.outgoing_messages.append(internal_message)
    

class BCSOut(BCSTrader):

    def first_move(self, **kwargs):
        self.leave_market()
        message_content = { 'group_id': self.market, 'type': 'leave_market', 
            'message': {'id': self.id_in_group }}
        internal_message = format_message('broadcast', **message_content)    
        self.outgoing_messages.append(internal_message)

class BCSSniper(BCSOut):

    def jump(self, **kwargs):
        is_positive_jump = super().jump(**kwargs)
        side = 'B' if is_positive_jump else 'S'
        host, port = self.exchange_host, self.exchange_port
        order_info = self.orderstore.enter(price=self.fp, buy_sell_indicator=side, 
                            time_in_force=0)
        delay = self.calc_delay()
        message_content = {'host': host, 'port': port, 'type': 'enter', 'delay':
                delay, 'order_info': order_info}
        internal_message = format_message('exchange', **message_content)
        self.outgoing_messages.append(internal_message)

class BCSInvestor(BCSOut):

    def invest(self, **kwargs):
        host, port = self.exchange_host, self.exchange_port
        order_side = kwargs['side']
        price = 2147483647  if order_side == 'B' else 0
        order_info = self.orderstore.enter(price=price, buy_sell_indicator=order_side, 
                                    time_in_force=0)
        message_content = {'host': host, 'port': port, 'type': 'enter', 'delay':
                0., 'order_info': order_info}
        internal_message = format_message('exchange', **message_content)
        self.outgoing_messages.append(internal_message)


class LEEPSInvestor(BCSOut):

    def invest(self, **kwargs):
        host, port = self.exchange_host, self.exchange_port
        #TODO: add logic to do some field checks asap.
        order_info = self.orderstore.enter(**kwargs)
        message_content = {'host': host, 'port': port, 'type': 'enter', 'delay':
                0., 'order_info': order_info}
        internal_message = format_message('exchange', **message_content)
        self.outgoing_messages.append(internal_message)
       


Sliders = namedtuple('Sliders', 'a_x a_y b_x b_y')

max_ask = 2147483647
min_bid = 0

class LEEPSBasicMaker(BCSTrader):

    def __init__(self, subject_state):
        super().__init__(subject_state)
        self.best_quotes = {'bid': None, 'offer': None}
        self.distance_from_best_quote = {'bid': None, 'offer': None}
    
    def first_move(self):
        self.leave_market()
        message_content = { 'group_id': self.market, 'type': 'leave_market', 
            'message': {'id': self.id_in_group }}
        internal_message = format_message('broadcast', **message_content)    
        self.outgoing_messages.append(internal_message)

    def calc_price(self, buy_sell_indicator, distance_from_best_quote=None):
        if distance_from_best_quote is None:
            d = self.distance_from_best_quote[buy_sell_indicator]
        best_quote = self.best_quotes[buy_sell_indicator]
        if buy_sell_indicator == 'B':
            price = best_quote - d
        elif buy_sell_indicator == 'S':
            price = best_quote + d
        return price
    
    def executed(self, **kwargs):
        order_info = self.orderstore.confirm('executed', **kwargs)
        buy_sell_indicator = order_info['buy_sell_indicator']
        price = self.calc_price(buy_sell_indicator)
        new_order_info = self.orderstore.enter(price=price, 
                buy_sell_indicator=buy_sell_indicator, time_in_force=99999)
        delay = self.calc_delay()
        host, port = self.exchange_host, self.exchange_port
        message_content = {'host': host, 'port': port, 'type': 'replace', 'delay':
                delay, 'order_info': new_order_info}
        internal_message = format_message('exchange', **message_content)
        self.outgoing_messages.append(internal_message)
 
    def trader_bid_offer_change(self, price=None, buy_sell_indicator=None, **kwargs):
        if buy_sell_indicator is None:
            buy_sell_indicator = kwargs.get('side')
        if price is None:
            price = price_grid(kwargs.get('price'))
            best_quote = self.best_quotes[buy_sell_indicator]
            d = abs(best_quote - price)
            self.distance_from_best_quote[buy_sell_indicator] = d
        orders = self.orderstore.all_orders()
        delay = self.calc_delay()
        if orders:
            for o in orders:
                existing_token = o['order_token']
                existing_buy_sell_indicator = o['buy_sell_indicator']
                if buy_sell_indicator == existing_buy_sell_indicator:
                    order_info = self.orderstore.register_replace(existing_token, price)
                    host, port = self.exchange_host, self.exchange_port
                    message_content = {'host': host, 'port': port, 'type': 'replace', 'delay':
                        delay, 'order_info': order_info}
                    internal_message = format_message('exchange', **message_content)
                    self.outgoing_messages.append(internal_message)
        else:
            order_info = self.orderstore.enter(price=price, 
                buy_sell_indicator=buy_sell_indicator, time_in_force=99999)
            host, port = self.exchange_host, self.exchange_port
            message_content = {'host': host, 'port': port, 'type': 'replace', 'delay':
                delay, 'order_info': order_info}
            internal_message = format_message('exchange', **message_content)
            self.outgoing_messages.append(internal_message)

    def bbo_update(self, **kwargs):
        new_best_bid, new_best_offer = kwargs['best_bid'], kwargs['best_ask']
        bbo = self.best_quotes
        existing_best_bid, existing_best_offer = bbo['bid'], bbo['offer']
        if new_best_bid != existing_best_bid:
            self.best_quotes['bid'] = new_best_bid
            d = self.distance_from_best_quote['bid']
            price = new_best_bid - d
            self.trader_bid_offer_change(price=price, buy_sell_indicator='B')
        if new_best_offer != existing_best_offer:
            self.best_quotes['offer'] = new_best_offer
            d = self.distance_from_best_quote['offer']
            price = new_best_offer + d
            self.trader_bid_offer_change(price=price, buy_sell_indicator='S')


class LEEPSNotSoBasicMaker(LEEPSBasicMaker):

    def __init__(self, subject_state):
        super().__init__(subject_state)
        self.latent_quote = None
        self.sliders = Sliders(a_x=0, a_y=0, b_x=0, b_y=0)
    
    def slider_change(self, lower_bound=-1, upper_bound=1, **kwargs):
        def slider_field_check(**kwargs):
            checked_kwargs = {}
            for k, v in kwargs.items():
                checked_value = int(v) 
                if v < - 1:
                    checked_value = -1
                elif v > 1:
                    checked_value = 1
                checked_kwargs[k] = checked_value
            return checked_kwargs
        fields = slider_field_check(**kwargs)
        new_slider = Sliders(**fields)
        old_slider = self.sliders
        if old_slider != new_slider:
            self.latent_quote_update(slider=new_slider)
               
    def latent_quote_update(self, latent_quote_formula=latent_bid_and_offer, sliders=None, **kwargs):
        if sliders is None:
            sliders = self.sliders
        best_bid = kwargs.get('best_bid')
        if best_bid is None:
            best_bid = self.best_quotes['bid']
        best_offer = kwargs.get('best_offer')
        if best_offer is None:
            best_offer = self.best_quotes['offer']
        order_imbalance = kwargs.get('order_imbalance')
        new_latent_quote = latent_quote_formula(best_bid, best_offer, order_imbalance, 
                self.orderstore.inventory)
        if new_latent_quote != self.latent_quote:
            bid = None
            offer = None
            old_bid, old_offer = self.latent_quote.copy()
            self.latent_quote = new_latent_quote
            new_bid, new_offer = new_latent_quote
            if new_bid != old_bid:
                bid = new_bid
            if new_offer != old_offer:
                offer = new_offer
            self.reprice(self, latent_bid=bid, latent_ask=offer)

    def reprice(self, latent_bid=None, latent_ask=None, start_from_above=True):
        orders = self.orderstore.all_orders()
        assert len(orders) <= 2, 'more than two orders in market: %s' % self.orderstore
        if orders:
            sorted_orders = sorted(orders, key=lambda order: order['price'], 
                                reverse=start_from_above)
            delay = self.calc_delay()
            for o in sorted_orders:
                token, buy_sell_indicator = o['order_token'], o['buy_sell_indicator']
                if latent_bid and buy_sell_indicator == 'B':
                    new_price = latent_bid
                    order_info = self.orderstore.register_replace(token, new_price)
                elif latent_ask and buy_sell_indicator == 'S':
                    new_price = latent_ask
                    order_info = self.orderstore.register_replace(token, new_price)
                host, port = self.exchange_host, self.exchange_port
                message_content = {'host': host, 'port': port, 'type': 'replace', 'delay':
                    delay, 'order_info': order_info}
                internal_message = format_message('exchange', **message_content)
                self.outgoing_messages.append(internal_message)
