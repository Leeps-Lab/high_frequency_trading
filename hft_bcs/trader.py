
from .decorators import atomic
import math
from .exchange import exchanges
import logging
from . import client_messages
from .utility import nanoseconds_since_midnight as labtime


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
    def get_trader(subject_state, orderstore, role_name):
        if role_name == 'sniper':
            return BCSCdaSniper(subject_state, orderstore)
        elif role_name == 'maker':
            return BCSMaker(subject_state, orderstore)
        elif role_name == 'out':
            return BCSOut(subject_state, orderstore)
        else:
            log.warning('unknown role: %s' % role_name)

class FBATraderFactory(TraderFactory):

    @staticmethod
    def get_trader(subject_state, orderstore, role_name):
        if role_name == 'sniper':
            return BCSFbaSniper(subject_state, orderstore)
        elif role_name == 'maker':
            return BCSMaker(subject_state, orderstore)
        elif role_name == 'out':
            return BCSOut(subject_state, orderstore)
        else:
            log.warning('unknown role: %s' % role_name)

class BaseTrader:

    state_spec = None

    client_message_dispatch = {}

    exchange_message_dispatch = {}

    group_message_dispatch = {}

    def __init__(self, subject_state, orderstore):
        for slot in subject_state.__slots__:
            setattr(self, slot, getattr(subject_state, slot))
        self.orderstore = orderstore
    
    def get_exchange_conn(self):
        assert self.exchange_address, 'exchange address is not set'
        try:
            conn = exchanges[self.exchange_address]
        except KeyError:
            log.warning('exchange connection not found at %s.' % self.exchange_address)
        return conn
    
    def get_state(self):
        state_class = self.state_spec
        kws = {slot: getattr(self, slot) for slot in self.state_spec.__slots__}
        subject_state = state_class(**kws)
        return subject_state

    def get_orderstore(self):
        return self.orderstore
    
    def receive_from_client(self, msg):
        msg_type = msg['type']
        methodname = self.client_message_dispatch[msg_type]
        getattr(self, methodname)(msg)
    
    def receive_from_group(self, header, body):
        handlers = self.group_message_dispatch
        methodname = handlers[header]
        getattr(self, methodname)(body)


class BCSTrader(BaseTrader):

    state_spec = BCSSubjectState

    short_delay = 0.1
    long_delay = 0.5

    client_message_dispatch = { 'spread_change': 'update_spread',
        'speed_change': 'update_speed'}
    
    group_message_dispatch = { 'A': 'handle_enter', 'U': 'handle_replace',
        'C': 'handle_cancel', 'E': 'handle_exec'}

    def first_move(self):
        pass

    def update_speed(self, message):
        """
        switch between slow and fast
        calculate cost if player turns off speed
        record time if player turns on speed
        """
        self.speed = not self.speed
        now = labtime()
        if self.speed:
            self.prev_speed_update = now
        else:
            start = self.prev_speed_update
            total_time = now - start
            self.prev_speed_update += total_time
        log_events.push(hfl.speed_update, **{'gid': self.group_id, 'pid': self.id, 'speed': self.speed})
        experiment_logger.log(SpeedLog(model=self))

    def orders_in_market(self):
        orders = self.orderstore.all_enters()
        orders_log = {
            'gid': self.group_id, 'pid': self.id, 'orders': orders
        }
        log_events.push(hfl.orders, **orders_log)
        counts = self.orderstore.counts() 
        count_log = {
            'gid': self.group_id, 'pid': self.id, 'act_count': counts['active'],
            'stg_count': counts['stage'],
        }
        log_events.push(hfl.order_count, **count_log)
        if len(orders) > 2:     # this has to hold if all works properly.
            log.warning('more than two enter orders: %s.' % orders)
        return orders

    def send_exchange(self, msgs, delay=False, speed=False):
        """
        msgs is a list of lists
        """
        msgs_flat = [m for msg in msgs for m in msg]
        true_msgs = filter(lambda x: x is not False, msgs_flat)
        if delay:
            dur = self.short_delay if speed else self.long_delay
        else:
            dur = 0.
        conn = self.get_exchange_conn().connection
        for m in true_msgs:
            conn.sendMessage(m, dur)
    
    def receive_from_group(self, header, body):
        super().receive_from_group(header, body)
        self.orders_in_market()
    
    def stage_enter(self, side=None, price=None, time_in_force=99999):
        spread = self.spread if side == 'S' else - self.spread
        price = math.ceil(self.fp + spread / 2) if not price else price
        order = self.orderstore.create(
            status='stage', side=side, price=price, time_in_force=time_in_force
        )
        log_dict = {
            'gid': self.group_id, 'pid': self.id, 'state': self.role,
            'speed': self.speed, 'order': order
        }
        log_events.push(hfl.stage_enter, **log_dict)
        kwargs = {'order_token': bytes(order.token, "utf-8"), 'buy_sell_indicator': bytes(order.side, "utf-8"),
            'price': order.price, 'time_in_force': order.time_in_force}
        ouch = BCSTranslator.encode('enter', **kwargs)
        return [ouch]
    
    def stage_replace(self, order):
        new_order, replace = self.replace(order)
        msgs = [translate.replace(o, new_order) for o in replace.values() 
                                                            if o is not False]
        log_dict = {
            'gid': self.group_id, 'pid': self.id, 'state': self.role,
            'speed': self.speed, 'head': replace['head'], 'new': new_order,
        }
        if len(msgs) > 1:
            log_dict['root'] = order
        log_events.push(hfl.stage_replace, **log_dict)
        return msgs

    def replace(self, order):
        spread = self.spread
        d = spread / 2 if order.side == 'S' else - spread / 2
        price = math.ceil(self.fp + d)
        new_order = self.orderstore.create(
            status='replace', side=order.side, price=price, time_in_force=99999
        )
        replace = {'root': order, 'head': False}
        # find the most recent update
        order_to_replace = self.orderstore.find_head(order)
        replace['head'] = order_to_replace
        # register the replace
        if order_to_replace is False:
            replace['root'] = False
        else:     
            order_to_replace.to_replace(new_order.token)
        if replace['root'] != replace['head']:
            # if order is already being replaced
            # we replace both the head and main order.
            order.to_replace(new_order.token)
        self.orderstore[order_to_replace.token] = order_to_replace
        self.orderstore[order.token] = order
        return (new_order, replace)
    
    def stage_cancel(self, order):
        """
        create a cancel order message
        return ouch message list
        """
        cancel = self.cancel(order)
        # TODO: translate cancel takes order.token,
        # translate replace takes order
        # make this uniform somehow
        msgs = [translate.cancel(o.token) for o in cancel.values()
                                                if o is not False]
        log_dict = {
            'gid': self.group_id, 'pid': self.id, 'state': self.role,
            'speed': self.speed, 'head': cancel['head'],
        }
        if len(msgs) > 1:
            log_dict['root'] = order
        return msgs
    
    def cancel(self, order):
        """
        does orderstore operations
        similar function to _replace
        """
        cancel = {'root': order, 'head': False}
        order_to_cancel = self.orderstore.find_head(order)
        cancel['head'] = order_to_cancel
        if order_to_cancel is False:
            # better log this each time each happens
            # made possible by design tho
            cancel['root'] = False
        return cancel
    
    def handle_enter(self, msg):
        """
        handle accept messages for the player
        update order status as active
        """
        timestamp, token = msg['timestamp'], msg['order_token']
        order = self.confirm_enter(timestamp, token)
        experiment_logger.log(EnterOrderLog(model=order, id=self.id, group_id=self.group_id))
        return order
    
    def handle_replace(self, msg):
        """
        handle replaced messages for the player
        """
        ptoken, token = msg['previous_order_token'], msg['replacement_order_token']
        timestamp = msg['timestamp']
        old_order, new_order = self.confirm_replace(timestamp, ptoken, token)
        experiment_logger.log(ReplaceOrderLog(model=self, replaced_roken=ptoken,
            new_token=token, timestamp=timestamp))
        return new_order
    
    def handle_exec(self, msg):
        """
        handles execution messages
        update order state as executed
        take profit
        """
        timestamp, tok = msg['timestamp'], msg['order_token']
        order = self.confirm_exec(timestamp, tok)
        price = msg['execution_price']
        profit = self.profit(price, order.side, timestamp)
        experiment_logger.log(ExecuteOrderLog(model=order, id=self.id, group_id=self.group_id))
        client_messages.broadcast(
            self.group_id,
            client_messages.execution(self.id_in_group, tok, profit)
        )
        return order

    def confirm_enter(self, timestamp, token):
        """
        orderstore operations when confirm
        """
        order = self.orderstore[token]
        if not order:
            log.warning('player %s: order %s not in active orders' % (self.id, token))
        # update order as active
        order = self.orderstore.activate(timestamp, order)
        log_events.push(hfl.confirm_enter, **{'gid': self.group_id, 'pid': self.id, 'order': order})
        return order
    
    def confirm_replace(self, timestamp, ptoken, token):
        old_order = self.orderstore[ptoken]
        new_order = self.orderstore[token]
        if not old_order:
            log.warning('player %s: order %s is not in active orders' % (self.id, ptoken))
        if not new_order:
            log.warning('player %s: order %s is not in active orders.' % (self.id, token))
        old_order = self.orderstore.inactivate(old_order, 'replaced')
        new_order = self.orderstore.activate(timestamp, new_order)
        log_dict = {'gid': self.group_id, 'pid': self.id, 'replaced': old_order, 'replacing': new_order}
        log_events.push(hfl.confirm_replace, **log_dict)
        return (old_order, new_order)
    
    def handle_cancel(self, msg):
        """
        handles canceled messages
        find canceled order in the order store
        move it to inactive dict
        update order state as canceled
        """
        timestamp, tok = msg['timestamp'], msg['order_token']
        order = self.confirm_cancel(timestamp, tok)
        experiment_logger.log(CancelOrderLog(model=order, id=self.id, group_id=self.group_id))

    def confirm_cancel(self, timestamp, token):
        order = self.orderstore[token]
        if not order:
            log.warning('player %s : canceled order %s not found in active orders.' % (self.id, token) )
        order = self.orderstore.inactivate(order, 'canceled')
        log_events.push(hfl.confirm_cancel, **{'gid': self.group_id, 'pid': self.id, 'order': order})
        return order

    def confirm_exec(self, timestamp, token):
        order = self.orderstore[token]
        order = self.orderstore.inactivate(order, 'executed')
        log_events.push(hfl.confirm_exec, **{'gid': self.group_id, 'pid': self.id, 'order': order})
        return order

    def leave_market(self):
        """
        exit market after switching from maker
        pass two ouch messages to cancel active orders
        """
        orders = self.orders_in_market()
        if orders:
            msgs = [self.stage_cancel(o) for o in orders]
            self.send_exchange(msgs, delay=True, speed=self.speed)
        else:
            log_events.push(hfl.no_orders, **{'gid': self.group_id, 'pid': self.id})
        client_messages.broadcast(
                self.group_id,
                client_messages.spread_change(self.id_in_group)
            )
    
    def profit(self, exec_price, side, timestamp):
        fp = self.fp
        d = abs(fp - exec_price)
        if exec_price < fp:
            # buyer (seller) buys (sells) less than fp
            pi = d if side == 'B' else -d  
        else:
            # seller (buyer) sells (buys) higher than fp
            pi = d if side == 'S' else -d  
        self.endowment += pi
        log_dict = {
            'gid': self.group_id, 'pid': self.id, 'amount': pi,
            'side': side, 'profit': self.endowment, 'fp': fp, 
            'p': exec_price,
        }
        log_events.push(hfl.profit, **log_dict)
        experiment_logger.log(ProfitLog(model=self, profit=pi))
        return pi   
    
    def take_cost(self, timestamp):
        """
        this should only be called once at session end
        can edit for different versions
        """
        if self.speed is True:
            self.update_speed('')   # sorry 
        delta = self.speed_on
        amount = self.speed_unit_cost * delta * 1e-9
        self.cost += amount
        log_dict = {
            'gid': self.group_id, 'pid': self.id,
            'amount': amount, 'delta': delta, 'cost': amount
        }
        log_events.push(hfl.cost, **log_dict)
        experiment_logger.log(CostLog(model=self))
        return self.cost
    
    def do_payoff(self):
        payoff = self.endowment - self.cost
        return (self.endowment, self.cost, payoff)

class BCSMaker(BCSTrader):

    def first_move(self):
        self.enter_market()

    def enter_market(self):
        """
        enter market after switching role to maker
        send two enter ouch messages to exchange via group
        """
        msgs = [self.stage_enter(side='B'), self.stage_enter(side='S')]
        self.send_exchange(msgs, delay=True, speed=self.speed)
    
    def makers_replace(self, flag):
        """
        implement makers' response to jumps and spread changes
        find active|staged orders
        compose replace messages
        flag determines the side of spread to replace first
        return ouch messages
        """
        orders = self.orders_in_market()
        sorted_orders = sorted(  # better to start from above if jump is positive.
            orders, key=lambda order: order.price, reverse=flag
        )
        msgs = [self.stage_replace(o) for o in sorted_orders]
        return msgs

    def handle_enter(self, msg):
        """
        handle accept messages for the player
        update order status as active
        """
        order = super().handle_enter(msg)
        self.makers_broadcast(order.token)
    
    def handle_replace(self, msg):
        """
        handle replaced messages for the player
        """
        new_order = super().handle_replace(msg)
        self.makers_broadcast(new_order.token)
    
    def handle_exec(self, msg):
        """
        handles execution messages
        update order state as executed
        take profit
        """
        order = super().handle_exec(msg)
        if order.time_in_force != 0:
            msgs = [self.stage_enter(side=order.side)]
            self.send_exchange(msgs, delay=True, speed=self.speed)

    def makers_broadcast(self, token):
        # message front-ends so they can place ticks
        # what is my fundamental price and spread ?
        # then these are legs
        lo, hi = self.fp - self.spread / 2, self.fp + self.spread / 2
        client_messages.broadcast(
            self.group_id,
            client_messages.spread_change(self.id_in_group, leg_up=hi, leg_low=lo, token=token)
        )

    def update_spread(self, message):
        """
        makers can change their spreads
        read new spread
        let all clients know
        replace existing orders with new price
        """
        new_spread = int(message['spread'])
        self.spread = new_spread
        msgs = self.makers_replace(1)  # replace orders, start from above
        self.send_exchange(msgs, delay=True, speed=self.speed)
        log_events.push(hfl.spread_update, ** {'gid': self.group_id, 'pid': self.id, 'spread': new_spread})
        experiment_logger.log(SpreadLog(model=self))
  
    # def jump(self, new_price):
    #     """
    #     player's response to jump
    #     update fundamental price
    #     return jump response to group.jump
    #     """
    #     is_positive = new_price - self.fp > 0.
    #     self.fp = new_price
    #     flag = 1 if is_positive else 0
    #     orders = self.makers_replace(flag)  # makers replace returns 2 ouch messages
    #     response = orders      
    #     return response

class BCSOut(BCSMaker):

    def first_move(self):
        self.leave_market()    
    
    def jump(self, new_price):
        self.fp = new_price

class BCSSniper(BCSTrader):

    def first_move(self):
        self.leave_market()

class BCSFbaSniper(BCSSniper):

    def jump(self, new_price):
        self.fp = new_price

class BCSCdaSniper(BCSSniper):

    def jump(self, new_price):
        """
        player's response to jump
        update fundamental price
        return jump response to group.jump
        """
        is_positive = new_price - self.fp > 0.
        self.fp = new_price
        side = 'B' if is_positive else 'S'
        order = [self.stage_enter(side=side, price=self.fp, time_in_force=0)]
        response = order
        return response
