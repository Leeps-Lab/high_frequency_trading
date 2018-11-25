
from .decorators import format_output
import math
from .exchange import exchanges
import logging
from . import client_messages
from .utility import nanoseconds_since_midnight


from . import translator as translate
from .subject_state import *
from .hft_logging.experiment_log import *
from .hft_logging.session_events import log_events
from .hft_logging import row_formatters as hfl
from .new_translator import BCSTranslator

log = logging.getLogger(__name__)


class TraderFactory:
    
    def get_trader(self):
        raise NotImplementedError()

class CDATraderFactory(TraderFactory):

    @staticmethod
    def get_trader(role_name, subject_state):
        if role_name == 'sniper':
            return BCSCdaSniper(subject_state)
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
            return BCSFbaSniper(subject_state)
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

    def receive(self, **kwargs) -> dict:
        """
        assumes arguments include key event_source
        """
        source = kwargs['event_source']
        lookup_key = kwargs['event_key']
        handler_name = self.message_dispatch[source][lookup_key]
        handler = getattr(self, handler_name)
        relevant_events = handler(**kwargs)
        return relevant_events

    def first_move(self):
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

    message_dispatch = {
     'client': {'spread_change': 'update_spread', 
        'speed_change': 'speed_change'},
     'exchange': {'A': 'accepted', 'U': 'replaced',
        'C': 'canceled', 'E': 'executed'}
    }

    @format_output
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
        if self.speed is True:
            time_since_speed_change = nanoseconds_since_midnight() - self.speed_on_start_time 
            if time_since_speed_change < 5 * 1e6:
                # otherwise the order of messages may break
                return delay
            delay = 0.1
        return delay

    def profit(self, buy_sell_indicator) -> int:
        fp = self.fp
        d = abs(fp - exec_price)
        if exec_price < fp:
            # buyer (seller) buys (sells) less than fp
            profit = d if buy_sell_indicator == 'B' else -d  
        else:
            # seller (buyer) sells (buys) higher than fp
            profit = d if buy_sell_indicator == 'S' else -d  
        return profit

    @format_output
    def jump(self, **kwargs):
        """
        base trader's response to a jump event
        update fundamental price
        """
        self.fp = int(kwargs['new_fundamental'])

    @format_output   
    def leave_market(self):
        """
        cancel all orders in market
        """
        orders = self.orderstore.all_orders()
        if orders:
            delay = self.delay()
            exchange_messages = [(b'cancel', delay, order_info) for order_info in orders]
        return {'exchange': exchange_messages}

    @format_output
    def accepted(self, **kwargs):
        self.orderstore.confirm('enter', **kwargs)

    @format_output
    def replaced(self, **kwargs):
        self.orderstore.confirm('replaced', **kwargs)  
     
    @format_output
    def canceled(self, **kwargs):
        self.orderstore.confirm('canceled', **kwargs)
        order_token = kwargs['order_token']
        broadcast_messages = []
        broadcast_info = ('canceled', {'id': self.id_in_group, 'order_token': order_token})
        broadcast_messages.append(broadcast_info)
        return {'broadcast': broadcast_messages}
    
    @format_output
    def executed(self, **kwargs):
        self.orderstore.confirm('executed', **kwargs)
        exec_price, side = kwargs['execution_price'], kwargs['buy_sell_indicator']
        order_token = kwargs['order_token']
        profit = self.profit(exec_price, side)
        self.endowment += profit
        broadcast_messages = []
        broadcast_info = ('executed', {'profit': profit, 'execution_price': exec_price,
            'order_token': order_token})
        broadcast_messages.append(broadcast_info)
        return {'broadcast': broadcast_messages}
            
            
class BCSMaker(BCSTrader):

    def calc_price(self, buy_sell_indicator):
        """
        return order price for a maker order based on spread
        """
        assert self.spread % 2 == 0
        leg_length = self.spread / 2
        multiplier = 1 if buy_sell_indicator == b'B' else -1
        price = self.fp + multiplier * leg_length
        return price

    @format_output
    def first_move(self):
        exchange_messages = []
        delay = self.delay()
        for side in (b'B', b'S'):
            price = self.calc_price(side)
            order_info = self.orderstore.enter(price=price, buy_sell_indicator=side, 
                            time_in_force=99999)
            exchange_messages.append((b'enter', delay, order_info))
        return {'exchange': exchange_messages}

    @format_output   
    def jump(self, **kwargs):
        """
        assumes trader has active/pending orders in market
        reprice orders
        replace sell order first if jump is positive
        """
        super().jump(**kwargs)
        positive_jump = kwargs['is_positive']
        # get list of active or pending orders
        exchange_messages = self.makers_reprice(positive_jump)
        return {'exchange': exchange_messages}
    
    def makers_reprice(self, start_from_above=True):
        orders = self.orderstore.all_orders()
        assert len(orders) <= 2, 'more than two orders in market: %s' % self.orderstore
        sorted_orders = sorted(orders, key=lambda order: order['price'], 
                            reverse=positive_jump)
        exchange_messages = []
        delay = self.calc_delay()
        for o in sorted_orders:
            token, buy_sell_indicator = o['order_token'], o['buy_sell_indicator']
            new_price = self.calc_price(buy_sell_indicator)
            order_info = self.orderstore.register_replace(token, new_price)
            exchange_messages.append((b'replace', delay, order_info))
        return exchange_messages   

    @format_output
    def spread_change(self, **kwargs):
        new_spread = int(kwargs['spread'])
        self.spread = new_spread
        exchange_messages = self.makers_reprice()
        return {'exchange': exchange_messages}
        
    def maker_broadcast_info(self, order_token):
        low_leg, high_leg = self.fp - self.spread / 2, self.fp + self.spread / 2
        broadcast_info = ('maker enter', {'low_leg': low_leg, 'high_leg': high_leg, 
            'order_token': order_token, 'id': self.id_in_group})        
        return broadcast_info

    @format_output
    def accepted(self, **kwargs):
        super().accepted(**kwargs)
        order_token = kwargs['order_token']
        broadcast_messages = []
        broadcast_info = self.maker_broadcast_info(self, order_token)
        broadcast_messages.append(broadcast_info)
        return {'broadcast': broadcast_messages}

    @format_output
    def replaced(self, **kwargs):
        super().replaced(**kwargs)  
        order_token = kwargs['order_token']
        broadcast_messages = []
        broadcast_info = self.maker_broadcast_info(self, order_token)
        broadcast_messages.append(broadcast_info)
        return {'broadcast': broadcast_messages}

    @format_output    
    def executed(self, **kwargs):
        broadcast_messages = super().executed(**kwargs)
        time_in_force = kwargs['time_in_force']
        side = kwargs['buy_sell_indicator']
        exchange_messages = []
        # make sure it is not a sniper order.
        if time_in_force != 0:
            price = self.calc_price(side)
            delay = self.calc_delay()
            order_info = self.orderstore.enter(price=price, buy_sell_indicator=side, 
                            time_in_force=99999)
            exchange_messages.append((b'enter', delay, order_info))
        return {'exchange': exchange_messages}.update(broadcast_messages)
    

class BCSOut(BCSTrader):

    def first_move(self):
        exchange_messages = self.leave_market()
        return {'exchange': exchange_messages}

class BCSSniper(BCSOut):

    @format_output
    def jump(self, **kwargs):
        super().jump(**kwargs)
        positive_jump = kwargs['is_positive']
        side = 'B' if positive_jump else 'S'
        exchange_messages = []
        order_info = self.orderstore.enter(price=self.fp, buy_sell_indicator=side, 
                            time_in_force=0)
        delay = self.calc_delay()
        exchange_messages.append((b'enter', delay, order_info))
        return {'exchange': exchange_messages}
        
        
        
    





            




        
