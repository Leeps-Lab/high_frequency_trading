import logging
import time
from . import hft_logging as hfl
log = logging.getLogger(__name__)

author = 'hasan ali demirci'
class OrderStore:
    def __init__(self, player_id, id_in_group):
        self.pid = player_id
        self.id_in_group = id_in_group
        self.count = 1
        self.active = dict()
        self.inactive = dict()

    def create(self, **kwargs):
        order = Order(self.id_in_group, self.count, **kwargs)
        self.active[order.token] = order
        self.count += 1
        return order
    
    def get_order(self, token):
        return self.active.pop(token, False)
    
    def find_order(self, token):
        try:
            out = self.active[token]
        except KeyError:
            out = False
            log_dict = {'pid': self.pid, 'token': token}
            hfl.logger.push(hfl.not_found, **log_dict)
        return out
  
    def get_all(self, state):
        return [v for v in self.active.values() if v.status == state]
    
    def find_head(self, order):
        """
        find most recent replace message for an order
        """
        new_head = order
        while self.is_replacing(new_head):
            new_head = self.find_order(new_head.replace_token)
        if isinstance(new_head, Order):
            l = '%s head is %s.' % (order.token, new_head.token)
            hfl.logger.push(hfl.order_head, **{ 'pid': self.pid, 'context': l})
        return new_head

    def is_replacing(self, order):
        out = False
        if order:
            out = order.replace_requested 
        return out

    def activate(self, time, order):
        order.activate(time)
        self.active[order.token] = order
        return order

    def cancel(self, time, order):
        order.cancel(time)
        self.inactive[order.token] = order
        return order

    def execute(self, time, order):
        order.execute(time)
        self.inactive[order.token] = order
        return order
        

    # def get_active(self, token):
    #     return self.active.pop(token, False)

    # def get_staged(self, token):
    #     return self.staged.pop(token, False)

    # def get_replace(self, token):
    #     return self.replace.pop(token, False)
    
    # def find_staged(self, token):
    #     return self.staged[token] 


class Order:
    
    def __init__(self, pid, count, **kwargs):
        self.pid = pid
        self.count = count
        self.price = kwargs['price']
        self.side = kwargs['side']
        self.time_in_force = kwargs['time_in_force']
        self.status = kwargs['status']
        self.replace_requested = False
        self.tokengen()

    def tokengen(self, prefix='SUB'):
        subject = str(chr(self.pid + 64))
        side = str(self.side)
        order_no = str(format(self.count, '09d'))
        self.token = prefix + subject + side  + order_no
        self.firm = prefix + subject

    def activate(self, time):
        if self.time_in_force == 0:
            self.status = 'SNI'
        else:
            self.status = 'ACT'
        self.timestamp = time
       
    def to_replace(self, time, replace_token):
        self.replace_requested = True
        self.replace_token = replace_token
        self.replace_req_time = time
 #       log.debug('Order %s: Register replace with %s.' % (self.token, self.replace_token))
    
    # def is_replacing(self):
    #     return self.replace_requested

    def cancel(self, time):
        self.status = 'XXX'
        self.time_canceled = time
   #     log.debug('Order %s is canceled and inactive.' % self.token)

    def execute(self, time):
        self.status = 'XXX'
        self.timestamp = time
  #      log.debug('Order %s executed and inactive.' % self.token)

    def __eq__(self, other_order):
        return self.token == other_order.token

    def __repr__(self):
        replace = 'none'
        if self.replace_requested:
            replace = self.replace_token
        out = '<Order {}:@{}:{}:{}:{}]>'.format(
            self.token, self.price, self.status, self.time_in_force, replace)
        return out
            







