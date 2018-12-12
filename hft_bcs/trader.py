
import math
import logging
from . import client_messages
from .utility import nanoseconds_since_midnight, ouch_fields


from collections import deque
from . import translator as translate
from .subject_state import *
from .hft_logging.experiment_log import *
from .hft_logging.session_events import log_events
from .hft_logging import row_formatters as hfl


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
        if not isinstance(subject_state, self.state_spec):
            raise TypeError('state x trader mismatch.')
        for slot in subject_state.__slots__:
            setattr(self, slot, getattr(subject_state, slot))
        self.outgoing_exchange_messages = deque()
        self.outgoing_broadcast_messages = deque()
        self.session_data = None

    def receive(self, **kwargs) -> dict:
        """
        assumes arguments include key event_source
        """
        lookup_key = kwargs['type']
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
        'E': 'executed', 'fundamental_price_change': 'jump'}

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
                exchange_message = (host, port, 'cancel', delay, order_info)
                self.outgoing_exchange_messages.append(exchange_message)

    def accepted(self, **kwargs):
        self.orderstore.confirm('enter', **kwargs)


    def replaced(self, **kwargs):
        self.orderstore.confirm('replaced', **kwargs)  
     

    def canceled(self, **kwargs):
        self.orderstore.confirm('canceled', **kwargs)
        order_token = kwargs['order_token']
        broadcast_info = ('canceled', self.group_id, {'id': self.id_in_group, 'order_token': order_token})
        self.outgoing_broadcast_messages.append(broadcast_info)
    
    def executed(self, **kwargs):
        order_info =  self.orderstore.confirm('executed', **kwargs)
        exec_price, side = kwargs['execution_price'], order_info['buy_sell_indicator']
        order_token = kwargs['order_token']
        profit = self.profit(exec_price, side)
        self.endowment += profit
        broadcast_info = ('executed', self.group_id, {'profit': profit, 'execution_price': exec_price,
            'order_token': order_token})
        self.outgoing_broadcast_messages.append(broadcast_info)
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
            self.outgoing_exchange_messages.append((host, port, 'enter', delay, order_info))

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
            self.outgoing_exchange_messages.append((host, port, 'replace', delay, order_info))

    def spread_change(self, **kwargs):
        new_spread = int(kwargs['spread'])
        self.spread = new_spread
        self.makers_reprice()

        
    def maker_broadcast_info(self, order_token):
        low_leg, high_leg = int(self.fp - self.spread / 2), int(self.fp + self.spread / 2)
        broadcast_info = ('maker_confirm', self.group_id, {'leg_up': high_leg, 'leg_low': low_leg, 
            'order_token': order_token, 'id': self.id_in_group})        
        self.outgoing_broadcast_messages.append(broadcast_info)

    def accepted(self, **kwargs):
        super().accepted(**kwargs)
        order_token = kwargs['order_token']
        broadcast_info = self.maker_broadcast_info(order_token)
        self.outgoing_broadcast_messages.append(broadcast_info)

    def replaced(self, **kwargs):
        super().replaced(**kwargs)  
        order_token = kwargs['replacement_order_token']
        broadcast_info = self.maker_broadcast_info(order_token)
        self.outgoing_broadcast_messages.append(broadcast_info)

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
            self.outgoing_exchange_messages.append((host, port, 'enter', delay, order_info))
    

class BCSOut(BCSTrader):

    def first_move(self, **kwargs):
        self.leave_market()
        broadcast_info = ('leave_market', self.group_id, {'id': self.id_in_group})
        self.outgoing_broadcast_messages.append(broadcast_info)

class BCSSniper(BCSOut):

    def jump(self, **kwargs):
        #TODO: keep fundamaental in environmental var
        is_positive_jump = super().jump(**kwargs)
        side = 'B' if is_positive_jump else 'S'
        host, port = self.exchange_host, self.exchange_port
        order_info = self.orderstore.enter(price=self.fp, buy_sell_indicator=side, 
                            time_in_force=0)
        delay = self.calc_delay()
        self.outgoing_exchange_messages.append((host, port, 'enter', delay, order_info))

class BCSInvestor(BCSOut):

    def invest(self, **kwargs):
        host, port = self.exchange_host, self.exchange_port
        order_side = kwargs['side']
        price = 2147483647  if order_side == 'B' else 0
        order_info = self.orderstore.enter(price=price, buy_sell_indicator=order_side, 
                                    time_in_force=0)
        self.outgoing_exchange_messages.append((host, port, 'enter', 0., order_info))


class LEEPSInvestor(BCSOut):

    def invest(self, **kwargs):
        host, port = self.exchange_host, self.exchange_port
        #TODO: add logic to do some field checks asap.
        order_info = self.orderstore.enter(**kwargs)
        self.outgoing_exchange_messages.append((host, port, 'enter', 0., order_info))
       
    



            




        
