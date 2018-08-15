import logging
import time
from .hft_logging import session_events as hfl
import itertools
from .utility import nanoseconds_since_midnight as labtime
from collections import namedtuple

log = logging.getLogger(__name__)

author = 'hasan ali demirci'

class OrderStore:
    typecode = 'bcs'
    status_set = ('stage', 'active', 'replace', 'sniper')
    enter_status = ('stage', 'active')


    def __init__(self, player_id, in_group_id):
        self.pid = player_id
        self.igid = in_group_id
        self.counter = itertools.count(1,1)
        self.orders = {}
        self.inactive = {}
    
    # TODO: add field validation for create.
    
    def create(self, **fields):
        count = next(self.counter)
        fields.update({'pid': self.pid, 'count': count, 'in_group_id': self.igid})
        order = Order(**fields)
        self.orders[order.token] = order
        return order
    
    def __getitem__(self, token):
        out = self.orders.get(token, False)
        if out is False:
            log_dict = {'pid': self.pid, 'token': token}
            hfl.events.push(hfl.not_found, **log_dict)
        return out
    
    def __setitem__(self, token, order):
        self.orders[token] = order
    
    def __str__(self):
        out = ' '
        out = out.join(str(order) for order in self.all_enters())
        return out
    
    def __len__(self):
        alles = self.all_enters()
        order_count = len(alles)
        return order_count
    
    def __format__(self, spec='count'):
        cls = self.__class__
        out = ''
        if spec == 'count':
            for status in cls.status_set:
                count = len(self.all_status(status))
                out.join('{status}:{count}'.format(status=status, count=count))
        return out

    def pop(self, token):
        return self.orders.pop(token)

    def all_status(self, status):
        if status not in self.__class__.status_set:
            raise ValueError('Invalid state.')
        out = [o for o in self.orders.values() if o.status == status]
        return out

    def all_enters(self):
        """
        returns all enter orders (staged/active)
        """
        cls = self.__class__
        out = [o for o in self.orders.values() if o.status in cls.enter_status
                                                    and o.time_in_force != 0 ]
        return out


    def find_head(self, order):
        """
        find most recent replace message for an order
        """
        head = order
        while getattr(head, 'replace_requested'):
            head = self.orders[head.replacer_token]
        if isinstance(head, Order):
            l = '%s head is %s.' % (order.token, head.token)
            hfl.events.push(hfl.order_head, **{'pid': self.pid, 'context': l})
        return head

    def activate(self, time, order):
        if order.time_in_force != 0:
            order.update(time, 'active')
        else:
            order.update(time, 'sniper')
        self.orders[order.token] = order
        return order
    
    def inactivate(self, order, reason):
        del self.orders[order.token]
        self.inactive[order.token] = (labtime(), reason)
        return order



class Order:
    typecode = 'nasdaq'
    __slots__ = (
        'pid', 'in_group_id', 'count', 'token', 'price', 'side', 
        'time_in_force', 'status', 'timestamp', 
        'firm', 'replace_requested', 'replacer_token'
    )
    prefix = 'SUB'
    core_fields = ('pid', 'in_group_id', 'count', 
        'price', 'side', 'time_in_force'
    )

    def __init__(self, **kwargs):
        for slot in self.__slots__:
            setattr(self, slot, kwargs.get(slot, False))
        self.tokengen()
    # TODO: check core fields

    def tokengen(self):
        cls = self.__class__
        subject = chr(int(self.in_group_id) + 64)
        side = self.side
        order_no = format(int(self.count), '09d')
        self.firm = cls.prefix + subject
        self.token = self.firm + side + order_no
    
    def update(self, time, status):
        self.status = status
        self.timestamp = time

    def __eq__(self, other_order):
        return self.token == other_order.token
    
    def to_replace(self, replacer_token):
        self.replace_requested = True
        self.replacer_token = replacer_token
    
    def __repr__(self):
        out = '<Order {self.token}:@{self.price}:{self.status}:{self.time_in_force}:{self.replacer_token}>'
        out = out.format(self=self)
        return out

    

    

# class OrderStore:
#     def __init__(self, player_id, id_in_group):
#         self.pid = player_id
#         self.id_in_group = id_in_group
#         self.counter = itertools.count()
#         self.active = dict()
#         self.inactive = dict()

#     def create(self, **fields):
#         count = next(self.counter)
#         order = Order(self.id_in_group, count, **fields)
#         self.active[order.token] = order
#         return order
    
#     def get_order(self, token):
#         return self.active.pop(token, False)
    
#     def find_order(self, token):
#         try:
#             out = self.active[token]
#         except KeyError:
#             out = False
#             log_dict = {'pid': self.pid, 'token': token}
#             hfl.events.push(hfl.not_found, **log_dict)
#         return out
  
#     def get_all(self, state):
#         return [v for v in self.active.values() if v.status == state]
    
#     def find_head(self, order):
#         """
#         find most recent replace message for an order
#         """
#         new_head = order
#         while self.is_replacing(new_head):
#             new_head = self.find_order(new_head.replace_token)
#         if isinstance(new_head, Order):
#             l = '%s head is %s.' % (order.token, new_head.token)
#             hfl.events.push(hfl.order_head, **{'pid': self.pid, 'context': l})
#         return new_head

#     def is_replacing(self, order):
#         out = False
#         if order:
#             out = order.replace_requested 
#         return out

#     def activate(self, time, order):
#         order.activate(time)
#         self.active[order.token] = order
#         return order

#     def cancel(self, time, order):
#         order.cancel(time)
#         self.inactive[order.token] = order
#         return order

#     def execute(self, time, order):
#         order.execute(time)
#         self.inactive[order.token] = order
#         return order

#     def __str__(self):
#         active = self.get_all('ACT')
#         stage = self.get_all('STG')
#         out = '{}:{}'.format(active, stage)
#         return out
        

    # def get_active(self, token):
    #     return self.active.pop(token, False)

    # def get_staged(self, token):
    #     return self.staged.pop(token, False)

    # def get_replace(self, token):
    #     return self.replace.pop(token, False)
    
    # def find_staged(self, token):
    #     return self.staged[token] 


# class Order:
    
#     def __init__(self, pid, count, **kwargs):
#         self.pid = pid
#         self.count = count
#         self.price = kwargs['price']
#         self.side = kwargs['side']
#         self.time_in_force = kwargs['time_in_force']
#         self.status = kwargs['status']
#         self.replace_requested = False
#         self.tokengen()

#     def tokengen(self, prefix='SUB'):
#         subject = str(chr(self.pid + 64))
#         side = str(self.side)
#         order_no = str(format(self.count, '09d'))
#         self.token = prefix + subject + side + order_no
#         self.firm = prefix + subject

#     def activate(self, time):
#         if self.time_in_force == 0:
#             self.status = 'SNI'
#         else:
#             self.status = 'ACT'
#         self.timestamp = time
       
#     def to_replace(self, time, replace_token):
#         self.replace_requested = True
#         self.replace_token = replace_token
#         self.replace_req_time = time
#  #       log.debug('Order %s: Register replace with %s.' % (self.token, self.replace_token))
    
#     # def is_replacing(self):
#     #     return self.replace_requested

#     def cancel(self, time):
#         self.status = 'XXX'
#         self.time_canceled = time
#    #     log.debug('Order %s is canceled and inactive.' % self.token)

#     def execute(self, time):
#         self.status = 'XXX'
#         self.timestamp = time
#   #      log.debug('Order %s executed and inactive.' % self.token)

#     def __eq__(self, other_order):
#         return self.token == other_order.token

#     def __repr__(self):
#         replace = 'none'
#         if self.replace_requested:
#             replace = self.replace_token
#         out = '<Order {}:@{}:{}:{}:{}]>'.format(
#             self.token, self.price, self.status, self.time_in_force, replace)
#         return out
            







