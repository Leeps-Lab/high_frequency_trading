
import logging

log = logging.getLogger(__name__)


class OrderStore:


    def __init__(self, player_id, id_in_group):
        self.pid = player_id
        self.id_in_group = id_in_group
        self.count = 1
        self.active = dict()
        self.inactive = dict()
        # self.active = dict()
        # self.staged = dict()
        # self.replace = dict()
        # self.inactive = dict()

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
            log.info('Order %s: Already inactive.' % token )
            out = False
        return out
        
    def get_all(self, state):
        return {k:v for k, v in self.active.items() if v.status == state}
    
    def find_head(self, order):
        """
        find most recent replace message for an order
        """
        new_head = order
        while self.is_replacing(new_head):
            new_head = self.find_order(new_head.replace_token)
        if isinstance(new_head, Order):
            log.debug('Order %s: Head is %s.' % (order.token, new_head.token))
        return new_head

    def is_replacing(self, order):
        out = False
        if order:
            out = order.replace_requested 
        return out

    def activate(self, time, order):
        order.activate(time)

    def cancel(self, time, order):
        order.cancel(time)
        self.inactive[order.token] = order


    def execute(self, time, order):
        order.execute(time)
        self.inactive[order.token] = order
        

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
        self.o_type = kwargs.get('o_type', 'n/a')
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
            self.status = 'sni'
            log.debug('Order %s: Activated as sniper.' % self.token )
        else:
            self.status = 'act'
            log.debug('Order %s: Activated as maker enter.' % self.token )
        self.timestamp = time
       
    def to_replace(self, time, replace_token):
        self.replace_requested = True
        self.replace_token = replace_token
        self.replace_req_time = time
        log.debug('Order %s: Register replace with %s.' % (self.token, self.replace_token))
    
    # def is_replacing(self):
    #     return self.replace_requested

    def cancel(self, time):
        self.status = 'cnc'
        self.time_canceled = time
        log.debug('Order %s is inactive.' % self.token)

    def execute(self, time):
        self.status = 'xxx'
        self.timestamp = time
        log.debug('Order %s executed and inactive.' % self.token)

    def __repr__(self):
        side = 'buy' if self.side == 'B' else 'sell'
        pid = str(self.pid)
        typ = self.o_type.lower()
        state = self.status
        if self.replace_requested:
            replace = self.replace_token
            repl_time = str(self.replace_req_time)
        else:
            replace = 'n/a'
            repl_time = 'n/a'
        price = str(self.price)
        out = (pid + ':' + side + ':' + typ + ':' + state + ':' + price  + ':' +
            replace + ':' + repl_time)
        return out
            







