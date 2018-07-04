
import logging

log = logging.getLogger(__name__)


class OrderStore:


    def __init__(self, player_id, id_in_group):
        self.pid = player_id
        self.id_in_group = id_in_group
        self.count = 1
        self.active = dict()
        self.staged = dict()
        self.inactive = dict()

    def create(self, **kwargs):
        order = Order(self.id_in_group, self.count, **kwargs)
        self.staged[order.token] = order
        self.count += 1
        return order

    def get_active_set(self):
        return self.active

    def get_active(self, token):
        return self.active.pop(token, False)

    def get_staged(self, token):
        return self.staged.pop(token, False)

    def activate(self, time, order):
        order.activate(time)
        self.active[order.token] = order
        log.debug('Order %s activated.' % order.token)
    
    def register_update(self, time , order, update_token):
        order.to_update(time, update_token)


    def cancel(self, time, order):
        order.cancel(time)
        self.inactive[order.token] = order
        log.debug('Order %s is inactive.' % order.token)

    def execute(self, time, order):
        order.execute(time)
        self.inactive[order.token] = order
        log.debug('Order %s executed and inactive.' % order.token)


class Order:
    
    def __init__(self, pid, count, **kwargs):
        self.pid = pid
        self.count = count
        self.price = kwargs['price']
        self.o_type = kwargs.get('o_type', None)
        self.side = kwargs['side']
        self.time_in_force = kwargs['time_in_force']
        self.status = 'S'
        self.update_requested = False
        self.tokengen()

    def tokengen(self, prefix='SUB'):
        subject = str(chr(self.pid + 64))
        side = str(self.side)
        order_no = str(format(self.count, '09d'))
        self.token = prefix + subject + side  + order_no
        self.firm = prefix + subject

    def activate(self, time):
        self.status = 'A'
        self.timestamp = time
    
    def to_update(self, time, update_token):
        self.update_requested = True
        self.update_req_time = time
        self.update_token = update_token

    def cancel(self, time):
        self.status = 'C'
        self.time_canceled = time

    def execute(self, time):
        self.status = 'X'
        self.timestamp = time

