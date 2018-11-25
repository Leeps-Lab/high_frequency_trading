import logging
import time
from .hft_logging import session_events as hfl
import itertools
from .utility import nanoseconds_since_midnight as labtime

log = logging.getLogger(__name__)

author = 'hasan ali demirci'

class OrderStore:
    token_prefix = 'SUB'
    order_format = '<Order{{ {order_token}:@{price}:{status}:{time_in_force}:{replacement_token} }}>'
    confirm_message_dispatch ={
        'enter': '_confirm_enter',
        'replace': '_confirm_replace',
        'cancel': '_confirm_cancel',
        'execution': '_confirm_execution'
    }

    def __init__(self, in_group_id):
        self.subject_code = chr(in_group_id + 64)
        self.counter = itertools.count(1,1)
        self._orders = {}
    
    @property
    def orders(self):
        return self._orders

    def enter(self, **kwargs):
        token = self.tokengen(**kwargs)
        kwargs['order_token'] = token 
        kwargs['status'] = b'pending'
        self._orders[token] = kwargs
        return kwargs
 
    def tokengen(self, **kwargs):
        count = next(self.counter)
        token = '{self.token_prefix}{self.subject_code}{buy_sell_indicator}{count:09d}'
        return token.format(self=self, count=count, **kwargs)

    def __getitem__(self, token):
        order_info = self._orders.get(token)
        return order_info

    def __str__(self):
        out = '\n'.join(self.order_format.format(**v) for v in self._orders.values())
        return out

    def all_orders(self):
        return [o for o in self._orders.values() if o['status'] in (b'active', b'pending')]
    
    def register_replace(self, token, new_price):
        order_info = self._orders[token]
        existing_token = order_info.get('replacement_order_token')
        if existing_token is None:
            existing_token = order_info['order_token']
        replacement_token = self.tokengen(**order_info)
        order_info['replacement_order_token'] = replacement_token
        # this field is added to comply with OUCH spec
        order_info['existing_order_token'] = existing_token
        order_info['replace_price'] = new_price
        self._orders[existing_token] = order_info
        return order_info
    
    def confirm(self, event_type, **kwargs):
        handler_name = self.confirm_message_dispatch[event_type]
        handler = getattr(self, handler_name)
        try:
            order_info = handler(self, **kwargs)
        except KeyError as e:
            log.exception(e)
        else:
            return order_info

    def _confirm_enter(self, **kwargs):
        token = kwargs['order_token']
        order_info = self._orders[token]
        order_info['status'] = b'active'
        order_info['timestamp'] = kwargs['timestamp']
        self._orders[token] = order_info
        return order_info    

    def _confirm_replace(self, **kwargs):
        existing_token = kwargs['previous_order_token']
        replacement_token = kwargs['replacement_order_token']
        order_info = self._orders[existing_token]
        order_info['order_token'] = replacement_token
        order_info['price'] = kwargs['price']
        if order_info['replacement_order_token'] == replacement_token:
            del order_info['replacement_order_token']
            del order_info['replace_price']
        return order_info   

    def _confirm_cancel(self, **kwargs):
        token = kwargs['order_token']
        del self._orders[token]
    
    def _confirm_execution(self, **kwargs):
        token = kwargs['order_token']
        del self._orders[token]       
    




