#!/usr/bin/env python
import subprocess
import os
import logging
import random
import time
import pandas as pd
from . import translator as translate
from .utility import nanoseconds_since_midnight as labtime
from . import exchange
from .profit import Price_Log, Price_Node
from channels import Group as CGroup, Channel
from otree.db.models import Model, ForeignKey
from otree.api import (
    models, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
)
import json
from django.core.cache import cache
from .order import Order, OrderStore
import time
log = logging.getLogger(__name__)

author = 'LEEPS Lab UCSC'

doc = """
Your app description
"""


class Constants(BaseConstants):
    name_in_url = 'oTree_HFT_CDA'
    players_per_group = 3
    num_rounds = 1
    speed_cost = 0.1 * (10 ** -6)

    inv_py = os.path.join(os.getcwd(), 'oTree_HFT_CDA/exos/investor.py')
    inv_url = 'ws://127.0.0.1:8000/hft_investor/'   
    inv_csv = os.path.join(os.getcwd(), 'raw/inv_test.csv')

    jump_py = os.path.join(os.getcwd(), 'oTree_HFT_CDA/exos/jump.py')
    jump_url = 'ws://127.0.0.1:8000/hft_jump/'   
    jump_csv = os.path.join(os.getcwd(), 'raw/jump_test.csv')


class Subsession(BaseSubsession):
    start_time = models.IntegerField()

    def creating_session(self):
        # location of Price_Log object
        cache.set('FP_Log', Price_Log(10), timeout=None)
        for i, group in enumerate(self.get_groups()):
            # Designating the first group as the authorized FPC updater
            if i == 0:
                cache.set('profit_pusher', group.id, timeout=None)           
            group.port = 9000 + i + 1
            group.json = {
                "messages": [],
            }
            group.save()
        self.session.save()


class Group(BaseGroup):

    port = models.IntegerField()

    def connect_to_exchange(self):
        log.info("Group%d: Connecting to exchange on port %d" % (self.id, self.port))
        exchange.connect(self, '127.0.0.1', self.port)
        log.info("Group%d: Connected to exchange on port %d" % (self.id, self.port))

    def disconnect_from_exchange(self):
        exchange.disconnect(self, '127.0.0.1', self.port)
        log.info("Group%d: Disconnected from exchange on port %d" % (self.id, self.port))

    def send_exchange(self, msgs, delay=False, speed=False):
        if delay:
            dur = (0.1 if speed else 0.5)
            log.info('Group%d: Delaying order: %f.' % (self.id, dur))
            time.sleep(dur)
        conn = exchange.connect(self, '127.0.0.1', self.port, wait_for_connection=True).connection
        for m in msgs:
            conn.sendMessage(m)

    def receive_from_exchange(self, msg):
        msg_type = (msg[0], len(msg))       # we use integer indexes since its the only option in this case
        try: 
            ouch = translate.get_types()[msg_type](msg)
            if ouch['type'] == 'S':
                return
        except KeyError:
            log.warning('Group{}: received type-{}:length-{}'.format(self.id, chr(msg[0]), len(msg)))
        if (ouch['order_token'][3] == '@'):
            if ouch['type'] == 'E':
                log.info('Group%d: Investor transacted.' % self.id)
            else:
                pass
        else:
            player = self.get_player_by_id(ord(ouch['order_token'][3]) - 64)
            player.receive_from_group(ouch)
        # do we want to save received messages ?
        # 
        # self.received['messages'].append(ouch)
        # self.save()

    def broadcast(self, note):
        """
        broadcast via channel layer
        """
        message = json.dumps(note)
        CGroup(str(self.id)).send({"text": message})

    def spawn(self, name, url, data):
        """
        fires exogenous processes
        as subprocess
        """
        log.info('Group%d: Fire %s.' % (self.id, name))
        cmd = ['python', name, str(self.id), url, data]
        subprocess.Popen(cmd)

    def jump_event(self, new_price):
        log.info('-----------Jump Start---------------')
        log.info('Group%d: Jump, new price is %d!' % (self.id, new_price) )

        # Check if group.id is the designated FPC updater
        if cache.get('profit_pusher') == self.id:
            # Push new profit to Price_Log
            fp_log = cache.get('FP_Log')
            fp_log.push(labtime(), new_price)
            cache.set('FP_Log', fp_log, timeout=None)

        self.broadcast({"FPC": new_price})

        players = self.get_players()
        player_responses = []
        fast_players = []
        slow_players = [] 

        for i, player in enumerate(players):
            response = player.jump(new_price)
            player_responses.append(response['order'])
            if response['order']:
                if response['speed']:
                    fast_players.append(i)
                else:
                    slow_players.append(i)      

        random.shuffle(fast_players)
        random.shuffle(slow_players)

        log.debug('Group%d: Jump: Delaying 0.1 seconds..' % self.id)
        time.sleep(0.1)

        log.info(
            'Group{}: fast players move order: {}'.format(self.id,  [i+1 for i in fast_players])
        )
        if fast_players:
            for i in fast_players:
                state = players[i].state
                pid = players[i].id_in_group
                log.debug(
                    'Group%d: fast %s player%d moves.' % (self.id, state, pid )
                )
                self.send_exchange(player_responses[i])

        log.debug('Group%d: Jump: Delaying 0.4 seconds more..' % self.id)
        time.sleep(0.4)

        log.info(
            'Group{}: slow players move order: {}'.format(self.id,  [i+1 for i in slow_players])
        )
        if slow_players:
            for i in slow_players:
                state = players[i].state
                pid = players[i].id_in_group
                log.debug(
                    'Group%d: slow %s player%d moves.' % (self.id, state, pid))
                self.send_exchange(player_responses[i])
        log.info('-----------Jump End---------------')



"""
why do we have this part, we never use jsonfield ?
"""

    # def save(self, *args, **kwargs):
    #     """
    #     JAMES
    #     BUG: Django save-the-change, which all oTree models inherit from,
    #     doesn't recognize changes to JSONField properties. So saving the model
    #     won't trigger a database save. This is a hack, but fixes it so any
    #     JSONFields get updated every save. oTree uses a forked version of
    #     save-the-change so a good alternative might be to fix that to recognize
    #     JSONFields (diff them at save time, maybe?).
    #     """
    #     super().save(*args, **kwargs)
    #     if self.pk is not None:
    #         json_fields = {}
    #         for field in self._meta.get_fields():
    #             if isinstance(field, JSONField):
    #                 json_fields[field.attname] = getattr(self, field.attname)
    #         self.__class__._default_manager.filter(pk=self.pk).update(**json_fields)

class Player(BasePlayer):

    # basic state variables
    state = models.StringField(initial='OUT')
    speed = models.BooleanField(initial=0)  # 0 or 1
    spread = models.IntegerField(initial=2000)
    channel = models.CharField(max_length=255)

    fp = models.IntegerField(initial=10000)
    order_count = models.IntegerField(initial=1)
    profit = models.IntegerField(initial=10000)
    time_of_speed_change = models.IntegerField()

    # Player actions

    def stage_enter(self, side, price=None, time_in_force=99999):
        """
        create an enter order
        default to maker enter order
        return the ouch message
        """  
        spread = (self.spread if side == 'S' else - self.spread)
        price = (int(self.fp + spread / 2) if not price else price)
        order = self._create_order(side=side, price=price, o_type='O', time_in_force=time_in_force)    
        ouch = translate.enter(order)
        log.info('Player%d: Stage: Enter %s: %s.' % (self.id_in_group, order.side, order.token))
        return ouch

    def stage_replace(self, order):
        """
        replace existing order
        create a new order 
        return a the ouch message
        """
        spread = (self.spread if order.side == 'S' else - self.spread)
        price = int(self.fp + spread / 2)
        new_order = self._create_order(side=order.side, price=price, time_in_force=99999)
        ouch = translate.replace(order, new_order)   
        log.info('Player%d: Stage: Replace: %s with %s.' % (self.id_in_group, order.token, new_order.token))
        return ouch

    def stage_cancel(self, order):
        """
        create a cancel order message
        return the ouch message
        """
        ouch = translate.cancel(order.token)
        log.info('Player%d: Stage: Cancel: %s.' % (self.id_in_group, order.token))
        return ouch

    def _create_order(self, **kwargs):
        """
        create a new order in player's order store
        save order store back in cache
        """
        orderstore = self.order_store()
        order = orderstore.create(**kwargs)
        self.save_order_store(orderstore)
        return order

    def _enter_market(self):
        """
        enter market after switching role to maker
        send two enter ouch messages to exchange via group
        """
        log.debug('Player%d: Enters market.' % (self.id_in_group)) 
        msgs = [self.stage_enter('B'), self.stage_enter('S')]
        self.group.send_exchange(msgs, delay=True, speed=self.speed)

    def _leave_market(self):
        """
        exit market after switching from maker
        pass two ouch messages to cancel active orders
        """
        self.group.broadcast({"SPRCHG":{self.id_in_group:0}})
        ords = self.order_store().get_active_set().values()
        if ords:
            msgs = [self.stage_cancel(o) for o in ords]
            self.group.send_exchange(msgs, delay=True, speed=self.speed)
        else:
            log.debug('Player%d: No active orders.' % self.id_in_group)
   
    # Client actions
    def update_state(self, message):
        """
        switch between 3 roles (states): OUT, SNIPER and MAKER
        """
        states = {
            'OUT':self._leave_market,
            'SNIPER':self._leave_market,
            'MAKER':self._enter_market
        }
        new_state = message['state']
        log.debug('Player%d: Start state update.' % (self.id_in_group)) 
        try:
            states[new_state]()
        except KeyError:    # like this is possible
            log.info('Player%d: Invalid state update.' % self.id_in_group)             
        self.state = new_state   
        self.save()
        log.info('Player%d: State is now: %s.' % (self.id_in_group, self.state)) 


    def update_spread(self, message):
        """
        makers can update their spreads
        read new spread 
        let all clients know
        replace existing orders with new price
        """
        self.spread = int(message['spread'])
        leg_low = self.fp - self.spread / 2
        leg_up = self.fp + self.spread / 2
        self.group.broadcast({
            "SPRCHG":{
                self.id_in_group: {
                    "B": leg_low, "A": leg_up}
                }
            })
        ords = self.order_store().get_active_set().values()
        log.debug('Player%d: Start spread change.' % (self.id_in_group)) 
        if ords:
            msgs = [self.stage_replace(o) for o in ords]
            self.group.send_exchange(msgs, delay=True, speed=self.speed)
        self.save()
        log.info('Player%d: Spread update: %s.' % (self.id_in_group, self.spread))

    def update_speed(self, message): 
        """
        switch between slow and fast
        calculate cost if player turns off speed
        record time if player turns on speed
        """  
        self.speed = not self.speed
        self.save()
        speed = ('fast' if self.speed else 'slow')
        log.info('Player%d: Speed change: %s.' % (self.id_in_group, speed))
        now = labtime()
        if self.speed:
            self.time_of_speed_change = now
        else:
            self._calc_speed_cost(now)
        self.save()

    """
    there are 3 possible client actions: 
    role change, spread change and state change
    """

    # Receive methods
    def receive_from_client(self, msg):
        """
        consumers call this when 
        oTree receives a websocket frame 
        from a client
        """

        actions= {
            'role_change':self.update_state,
            'spread_change':self.update_spread,
            'speed_change':self.update_speed
        }
        actions[msg['type']](msg)


    def receive_from_group(self, msg):
        events= {
            'A':self.confirm_enter,
            'U':self.confirm_replace,
            'C':self.confirm_cancel,
            'E':self.confirm_exec
        }
        events[msg['type']](msg)

    """
    update order_store when
    player receives a message
    from the exchange
    """

    # Confirm methods    

    # These methods should send response to clients ! 

    def confirm_enter(self,msg):
        """
        handle accept messages for the player
        update order status as active
        """
        stamp, tok = msg['timestamp'], msg['order_token']
        orderstore = self.order_store()
        order = orderstore.get_staged(tok)
        assert order    # I should get rid of these asserts after testing
        orderstore.activate(stamp, order)
        log.info('Player%d: Confirm: Enter: %s.' % (self.id_in_group, tok))
        self.save_order_store(orderstore)

    def confirm_replace(self, msg):
        """
        handle replaced messages for the player
        """
        ptok, tok = msg['previous_order_token'], msg['order_token']
        stamp = msg['timestamp']
        orderstore = self.order_store()
        old_order = orderstore.get_active(ptok)
        assert old_order
        new_order = orderstore.get_staged(tok)
        assert new_order
        orderstore.cancel(stamp, old_order)
        orderstore.activate(stamp, new_order)
        self.save_order_store(orderstore)
        log.info('Player%d: Confirm: Replace %s with %s.' % (self.id_in_group, ptok, tok))

    def confirm_cancel(self, msg):
        """
        handles canceled messages for the player
        find canceled order in the order store
        move it to inactive dict
        update order state as canceled
        """
        stamp, tok = msg['timestamp'], msg['order_token']
        orderstore = self.order_store()
        order = orderstore.get_active(tok)
        assert order
        orderstore.cancel(stamp, order)
        self.save_order_store(orderstore)        
        log.info('Player%d: Confirm: Cancel %s.' % (self.id_in_group, tok))

    def confirm_exec(self,msg):
        """
        handles canceled messages for the player
        update order state as executed
        take profit
        """
        stamp, tok = msg['timestamp'], msg['order_token']
        price = msg['price']
        orderstore = self.order_store()
        order = orderstore.get_active(tok)
        orderstore.execute(stamp, order)
        self.save_order_store(orderstore) 
        log.info('Player%d: Confirm: Transaction: %s.' % (self.id_in_group, tok))
        profit = self.calc_profit(price, order.side, stamp) 
        log.info('Player%d: Take Transaction Profit: %d.' % (self.id_in_group, profit))
        self.group.broadcast({
            "EXEC": {
                "id": self.id_in_group, "token": tok, "profit": profit}
            })
        if self.state == 'MAKER':
             log.debug('Player%d: Execution action: Enter a new order.' % self.id_in_group)
             m = [self.stage_enter(order.side)]
             self.group.send_exchange(m, delay=True, speed=self.speed)

    def calc_profit(self, exec_price, side, timestamp):
        """
        find the distance btw fundamental and execution prices
        order side determines profit sign
        log speed cost along the way
        """
        fp = cache.get('FP_Log').getFP(timestamp)
        d = abs(fp - exec_price)
        if exec_price < fp:
            pi = d if side == 'B' else -d
        else:
            pi = d if side == 'S' else -d
        self.profit += pi
        if self.speed:
            self._calc_speed_cost(labtime())
        self.save()
        return pi
    
    def _calc_speed_cost(self, timestamp):
        """
        calculate speed cost since the previous calculation
        """
        delta = timestamp - self.time_of_speed_change
        cost = delta * Constants.speed_cost
        self.time_of_speed_change = timestamp
        self.profit -= cost
        log.info('Player%d: Take speed cost: %d' % (self.id_in_group, cost))

    # def calc_profit(self, exec_price, side, timestamp):
    #     profit = 0
    #     fp = cache.get('FP_Log').getFP(timestamp)

    #     if side == 'B':
    #         # Execution of your buy offer
    #         if exec_price < fp:                  #  Player bought lower than FP (positive profit)
    #             profit += abs(fp - exec_price)
    #             if self.speed == 1:
    #                 time_temp = Get_Time()
    #                 self.calc_speed(0, Get_Time())
    #                 self.calc_speed(1, Get_Time())
    #         else:                                #  Player bought higher than FP (negative profit)   
    #             profit -= abs(fp - exec_price)   
    #             if self.speed == 1:
    #                 time_temp = Get_Time()
    #                 self.calc_speed(0, Get_Time())
    #                 self.calc_speed(1, Get_Time())
    #     else:
    #         # Execution of your sell offer
    #         if exec_price < fp:                  #  Player sold lower than FP (negative profit)
    #             profit -= abs(fp - exec_price) 
    #             if self.speed == 1:
    #                 time_temp = Get_Time()
    #                 self.calc_speed(0, Get_Time())
    #                 self.calc_speed(1, Get_Time())
    #         else:
    #             profit += abs(fp - exec_price)      #  Player sold higher than FP (positive profit)
    #             if self.speed == 1:
    #                 time_temp = Get_Time()
    #                 self.calc_speed(0, Get_Time())
    #                 self.calc_speed(1, Get_Time())
    #     self.profit += profit
    #     self.save()
    #     return profit


    # # state = True/False (speed on/speed off) timestamp = time of speed state change
    # def calc_speed(self, state, timestamp):
    #     if state == 1:
    #         self.time_of_speed_change = Get_Time()
    #     else:
    #         self.profit -= (timestamp - self.time_of_speed_change) * Constants.speed_cost
    #         self.save()

    def jump(self, new_price):
        is_positive = new_price - self.fp
        self.fp = new_price 
        self.save()
        response = {'order': False, 'speed': self.speed}

        if self.state == 'SNIPER':
            log.debug('Player%d: Jump Action: Snipe.' % self.id_in_group)
            side = 'B' if is_positive else 'S'
            order = [self.stage_enter(side, price=self.fp, time_in_force=0)]
            response['order'] = order
        elif self.state == 'MAKER':
            log.debug('Player%d: Jump Action: Replace orders.' % self.id_in_group)
            flag = 1 if is_positive else 0
            orders = self._adjust_price(flag)
            response['order'] = orders
        else:
            log.debug('Player%d: Jump Action: Nothing to do.' % self.id_in_group)
        return response


    # def jump(self, new_price):  
    #     old_fp = self.fp              
    #     self.fp = new_price
    #     self.save()
    #     postive_jump = (self.fp - old_fp) > 0

    #     if self.state == 'OUT':
    #         log.debug('Player%d: Jump Action: Nothing to do.' % self.id_in_group)
    #         return [None, self.speed]

    #     elif self.state == 'SNIPER':
    #         log.debug('Player%d: Jump Action: Snipe.' % self.id_in_group)
    #         side = ('B' if postive_jump else 'S')
    #         order = [self.stage_enter(side, price=self.fp, time_in_force=0)]  # Special value for a market order
    #         return [order, self.speed]

    #     else:
    #         log.debug('Player%d: Jump Action: Replace orders.' % self.id_in_group)
    #         flag = (1 if postive_jump else 0)
    #         orders = self._adjust_price(flag)
    #         return [orders, self.speed]


    def _adjust_price(self, flag):
        """
        implement makers response to jumps
        find active orders
        compose replace messages
        return ouch messages
        """
        ords = self.order_store().get_active_set().values()
        if ords:    # have to start from above if jump is positive
            sorted_ords = sorted(
                ords, key=lambda order: order.price, reverse=flag
            )
            msgs = [self.stage_replace(o) for o in sorted_ords]
            return msgs
        else:
            pass


    """
    send message to the client after event or operation
    """

    # Send to client

    def send_client(self,msg):
        """
        to front_end
        message has to be a dictionary
        """
        message = json.dumps(msg)
        Channel(self.channel).send({"text": message})


    """
    extra storage for the player
    """

    def order_store(self):
        """
        player's order store
        lives in cache backend
        """
        order_store = cache.get(self.id)
        if not order_store:
            log.info('Player%d: Create Order Store.' % self.id_in_group)
            order_store = OrderStore(self.id, self.id_in_group)
            cache.set(self.id, order_store, timeout=None)
        return order_store

    def save_order_store(self, orderstore):
        """
        write to cache
        """
        cache.set(self.id, orderstore, timeout=None)


class Investor(Model):

    group = ForeignKey(Group)
    order_count = models.IntegerField(initial=1)

    def receive_from_consumer(self, side):
        s = ('Buy' if side=='B' else 'Sell')
        log.info('Investor: %s.' % s)
        self.invest(side)

    def invest(self, side):
        p = (214748.3647 if side == 'B' else 0)
        order = Order(0, self.order_count, side=side, price=p, time_in_force=0)
        ouch = translate.enter(order)
        log.debug('Investor sends an order: %s' % order.token)
        self.group.send_exchange([ouch])
        self.order_count += 1
        self.save()
