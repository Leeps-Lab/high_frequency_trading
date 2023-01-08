import logging
import time
import itertools

log = logging.getLogger(__name__)


class OrderStore:
    # single stock orderstore
    # expects keys as in OUCH
    token_format = '{self.firm}{buy_sell_indicator}{self.player_id:04d}{count:05d}'
    confirm_message_dispatch ={
        'enter': '_confirm_enter',
        'replaced': '_confirm_replace',
        'canceled': '_confirm_cancel',
        'executed': '_confirm_execution'
    }

    def __init__(self, player_id: int, in_group_id=None, firm=None, default_shares=1,
            ticker=b'AMAZGOOG', default_inventory=0, **kwargs):
        if in_group_id == firm == None:
            raise Exception('in_group_id and firm kwargs are both None')
        self.ticker = ticker
        self.order_counter = itertools.count(1,1)
        self.player_id = player_id
        self.default_shares = default_shares
        self.firm = firm or chr(in_group_id + 64) * 4
        self._orders = {}
        self._pre_orders = {}
        self.inventory = default_inventory
        self.bid = None
        self.offer = None
        
        self.total_bids = 0
        self.total_asks = 0
        self.sum_bid_price = 0
        self.sum_ask_price = 0
        

    @property
    def orders(self):
        return self._orders

    def enter(self, **kwargs):
        kwargs['created_at'] = time.time()
        kwargs['status'] = b'pending'
        kwargs['firm'] = self.firm
        if 'shares' not in kwargs:
            kwargs['shares'] = self.default_shares
        kwargs['stock'] = self.ticker
        token = self.tokengen(**kwargs)
        kwargs['order_token'] = token 
        self._orders[token] = kwargs
        log.debug('trader %s: register enter: token: %s, price: %s.' % (
            self.player_id, token, kwargs['price']))
        return kwargs
    
    def tokengen(self, **kwargs):
        count = next(self.order_counter)
        return self.token_format.format(self=self, count=count, **kwargs)

    def __getitem__(self, token):
        order_info = self._orders.get(token)
        return order_info

    def __str__(self):
        active_orders = '\n'.join(str(v) for v in self._orders.values() if v['status'] == b'active')
        pending_orders = '\n'.join(str(v) for v in self._orders.values() if v['status'] == b'pending')
        ioc = '\n'.join(str(v) for v in self._orders.values() if v['status'] == b'ioc')       
        out = """Player {self.player_id} Orders:
                Active:
{active_orders}

                IOC: 
{ioc_orders}

                Pending:
{pending_orders}          

            
Spread: {self.bid} - {self.offer}
     """.format(self=self, active_orders=active_orders, pending_orders=
            pending_orders, ioc_orders=ioc)
        return out

    def all_orders(self, direction=None):
        out = [o for o in self._orders.values() if o['status'] 
            in (b'active', b'pending')]
        if direction is None:
            return out
        else:
            out = list(filter(lambda x: x['buy_sell_indicator'] == direction, out))
            return out
    
    def all_pre_orders(self, direction=None):
        out = [o for o in self._pre_orders.values() if o['status'] 
            in (b'active', b'pending')]
        if direction is None:
            return out
        else:
            out = list(filter(lambda x: x['buy_sell_indicator'] == direction, out))
            return out

    def register_replace(self, token, new_price):
        try:
            order_info = self._orders[token]
        except KeyError:
            log.error('error register replace for token: %s, orderstore: %s' % (token, self))
            raise
        existing_token = order_info.get('replacement_order_token')
        if existing_token is None:
            existing_token = order_info['order_token']
        replacement_token = self.tokengen(**order_info)
        # this field is added to comply with OUCH spec
        order_info['existing_order_token'] = existing_token
        order_info['replacement_order_token'] = replacement_token
        order_info['replace_price'] = new_price
        self._orders[token] = order_info

        pre_order_info = order_info
        pre_order_info['order_token'] = replacement_token
        old_price = int(pre_order_info['price'])    
        pre_order_info['price'] = new_price
        pre_order_info['old_price'] = old_price
        self._pre_orders[replacement_token] = pre_order_info

        log.debug('trader %s: register replace for token %s with %s at price %s.' % (
            self.player_id, existing_token, replacement_token, new_price))
        return order_info
    
    def confirm(self, event_type, **kwargs):
        handler_name = self.confirm_message_dispatch[event_type]
        handler = getattr(self, handler_name)
        try:
            order_info = handler(**kwargs)
        except:
            log.exception("""
            error during orderstore confirm operation: "%s" 
            message: %s 
            orderstore: %s
""" % (handler_name, kwargs, self))
            raise
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
        order_info['confirmed_at'] = time.time()
        travel_time =  round(order_info['confirmed_at'] - 
            order_info['created_at'], 4)
        order_info['travel_time'] = travel_time
        self._orders[token] = order_info
        price = order_info['price']
        direction = order_info['buy_sell_indicator']
        log.debug('trader %s: confirm enter: token %s.' % (self.player_id, token))
        log.debug('order %s travel time %s' % (token, travel_time))
        self.update_spread(price, direction)
        return order_info    

    def _confirm_replace(self, **kwargs):
        existing_token = kwargs['previous_order_token']
        replacement_token = kwargs['replacement_order_token']
        order_info = self._orders.get(existing_token)
        replacement_order = self._pre_orders[replacement_token]

        if order_info is not None:
            new_price = kwargs['price']
            old_price = int(order_info['old_price'])
            replacement_order['price'] = new_price
            replacement_order['old_price'] = old_price
            self._orders.pop(existing_token)

            if replacement_order['replacement_order_token'] == replacement_token:
                del order_info['replacement_order_token']
                del order_info['replace_price']
            self._orders[replacement_token] = replacement_order
            self._pre_orders.pop(replacement_token)
            direction = replacement_order['buy_sell_indicator']
            self.update_spread(old_price, direction, clear=True)
            self.update_spread(new_price, direction)
        
        log.debug('trader %s: confirm replace: token %s --> %s.' % (self.player_id, 
            existing_token, replacement_token))
        return replacement_order   

    def _confirm_cancel(self, **kwargs):
        token = kwargs['order_token']
        order_info = self._orders.pop(token)
        direction = order_info['buy_sell_indicator']
        price = order_info['price']
        self.update_spread(price, direction, clear=True)   
        log.debug('trader %s: confirm cancel: token %s.' % (self.player_id, token))
        return order_info
    
    def _confirm_execution(self, **kwargs):
        token = kwargs['order_token']
        order_info = self._orders.pop(token)
        direction = order_info['buy_sell_indicator']
        shares = kwargs['executed_shares']
        self.inventory += shares if direction == 'B' else - shares
        price = order_info['price']
        log.debug('trader %s: confirm execution: token %s.' % (self.player_id, token))
        self.update_spread(price, direction, clear=True)      

        '''
        if direction == 'B':
            self.totalBids += shares
            self.sumBidPrice += price  
        else:
            self.totalAsks += shares
            self.sumAskPrice += price  
        '''
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