import logging
import time
from .hft_logging import session_events as hfl
from .utility import nanoseconds_since_midnight
import itertools

log = logging.getLogger(__name__)

class OrderStore:
    token_prefix = 'SUB'
    order_format = '<Order{{ {order_token}:@{price}:{status}:{time_in_force} }}>'
    confirm_message_dispatch ={
        'enter': '_confirm_enter',
        'replaced': '_confirm_replace',
        'canceled': '_confirm_cancel',
        'executed': '_confirm_execution'
    }

    def __init__(self, pid, in_group_id):
        self.player_id = pid
        self.subject_code = chr(int(in_group_id) + 64)
        self.counter = itertools.count(1,1)
        self._orders = {}
        self.inventory = 0
        self.bid = None
        self.offer = None
    @property
    def orders(self):
        return self._orders

    def enter(self, **kwargs):
        token = self.tokengen(**kwargs)
        kwargs['order_token'] = token 
        kwargs['status'] = b'pending'
        kwargs['created_at'] = nanoseconds_since_midnight()
        self._orders[token] = kwargs
        return kwargs
 
    def tokengen(self, **kwargs):
        count = next(self.counter)
        token = '{self.token_prefix}{self.subject_code}{buy_sell_indicator}{self.player_id:04d}{count:05d}'
        return token.format(self=self, count=count, **kwargs)

    def __getitem__(self, token):
        order_info = self._orders.get(token)
        return order_info

    def __str__(self):
        active_orders = '\n\t\t\t'.join(str(v) for v in self._orders.values() if v['status'] == b'active')
        pending_orders = '\n\t\t\t'.join(str(v) for v in self._orders.values() if v['status'] == b'pending')
        ioc = '\n\t\t\t'.join(str(v) for v in self._orders.values() if v['status'] == b'ioc')       
        out = """Player {self.player_id} Orders:
                Active:{active_orders}

                IOC: {ioc_orders}

                Pending:{pending_orders}
                
            Spread: {self.bid} - {self.offer}
     """.format(self=self, active_orders=active_orders, pending_orders=
            pending_orders, ioc=ioc)
        return out

    def all_orders(self, direction=None):
        out = [o for o in self._orders.values() if o['status'] 
            in (b'active', b'pending')]
        if direction is None:
            return out
        else:
            out = list(filter(lambda x: x['buy_sell_indicator'] == direction, out))
            return out

    def register_replace(self, token, new_price):
        order_info = self._orders[token]
        existing_token = order_info.get('replacement_order_token')
        if existing_token is None:
            existing_token = order_info['order_token']
        replacement_token = self.tokengen(**order_info)
        # this field is added to comply with OUCH spec
        order_info['existing_order_token'] = existing_token
        order_info['replacement_order_token'] = replacement_token
        order_info['replace_price'] = new_price
        self._orders[existing_token] = order_info
        return order_info
    
    def confirm(self, event_type, **kwargs):
        handler_name = self.confirm_message_dispatch[event_type]
        handler = getattr(self, handler_name)
        try:
            order_info = handler(**kwargs)
        except KeyError as e:
            log.exception(e)
        else:
            return order_info

    def _confirm_enter(self, **kwargs):
        token = kwargs['order_token']
        order_info = self._orders[token]
        time_in_force = kwargs['time_in_force']
        if time_in_force != 0:
            order_info['status'] = b'active'
        else:
            order_info['status'] = b'ioc'
        order_info['timestamp'] = kwargs['timestamp']
        order_info['confirmed_at'] = nanoseconds_since_midnight()
        self._orders[token] = order_info
        price = order_info['price']
        direction = order_info['buy_sell_indicator']
        self.update_spread(price, direction)
        return order_info    

    def _confirm_replace(self, **kwargs):
        existing_token = kwargs['previous_order_token']
        replacement_token = kwargs['replacement_order_token']
        order_info = self._orders.pop(existing_token)
        order_info['order_token'] = replacement_token
        new_price = kwargs['price']
        old_price = int(order_info['price'])
        direction = order_info['buy_sell_indicator']
        self.update_spread(old_price, direction, clear=True)
        self.update_spread(new_price, direction)
        
        if order_info['replacement_order_token'] == replacement_token:
            del order_info['replacement_order_token']
            del order_info['replace_price']
        order_info['price'] = new_price
        self._orders[replacement_token] = order_info
        order_info['old_price'] = old_price
        return order_info   

    def _confirm_cancel(self, **kwargs):
        token = kwargs['order_token']
        order_info = self._orders.pop(token)
        direction = order_info['buy_sell_indicator']
        price = order_info['price']
        self.update_spread(price, direction, clear=True)   
        return order_info

    
    def _confirm_execution(self, **kwargs):
        token = kwargs['order_token']
        order_info = self._orders.pop(token)
        direction = order_info['buy_sell_indicator']
        inventory_change = 1 if direction == b'B' else -1
        self.inventory += inventory_change
        price = order_info['price']
        self.update_spread(price, direction, clear=True)            
        return order_info

    def update_spread(self, price, direction, clear=False):
        if direction == 'B':
            if clear is True and price == self.bid:
                self.bid = None
            elif price is not None and (self.bid is None or price > self.bid):
                self.bid = price
        elif direction == 'S':
            if clear is True and price == self.offer:
                self.offer = None
            elif price is not None and (self.offer is None or price < self.offer):
                self.offer = price   