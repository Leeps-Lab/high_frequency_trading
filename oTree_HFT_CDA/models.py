#!/usr/bin/env python
import subprocess
import os
import logging
import random
import time
from . import translator as translate
from .exp_logging import prepare
from .utility import nanoseconds_since_midnight as labtime
from . import exchange
from .profit import Price_Log, Price_Node
from channels import Group as CGroup, Channel
from otree.db.models import Model, ForeignKey
from otree.api import (
    models, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
)
from .client_message import ClientMessage
import json
from django.core.cache import cache
from .order import Order, OrderStore
import time
log = logging.getLogger(__name__)
from twisted.internet import reactor
author = 'LEEPS Lab UCSC'

doc = """
Your app description
"""


class Constants(BaseConstants):
    name_in_url = 'oTree_HFT_CDA'
    players_per_group = None
    num_rounds = 1

    # speed_cost = 0.1 * (1e-5)   
    # default_fp = 10 ** 6    #   default fundamental price

    # exc_host = '127.0.0.1'  # ip of exchange hosting machine

    short_delay = 0.1   # slow players delay
    long_delay = 0.5    # fast players delay

    investor_url = 'ws://127.0.0.1:8000/hft_investor/'
    jump_url = 'ws://127.0.0.1:8000/hft_jump/'

    investor_py = os.path.join(os.getcwd(), 'oTree_HFT_CDA/exos/investor.py')
    jump_py = os.path.join(os.getcwd(), 'oTree_HFT_CDA/exos/jump.py')


class Subsession(BaseSubsession):
    start_time = models.BigIntegerField()
    players_per_group = models.IntegerField()

    def creating_session(self):
        # configurable group size, copy from oTree docs.
        group_matrix = []
        players = self.get_players()
        ppg = self.session.config['players_per_group']
        self.players_per_group = ppg
        for i in range(0, len(players), ppg):
            group_matrix.append(players[i:i+ppg])
        self.set_group_matrix(group_matrix)

        # location of Price_Log object
        cache.set('FP_Log', Price_Log(10), timeout=None)

        for i, g in enumerate(self.get_groups()):
            # designating the first group as the authorized FPC updater
            if i == 0:
                cache.set('profit_pusher', g.id, timeout=None) 
            # set exchange host and port to connect
            g.exch_host = self.session.config['exchange_host']
            g.exch_port = 9000 + i + 1
            # read in investor and jump arrival times
            investors = 'investors_group_' + str(i + 1)  # hacking
            jumps = 'jumps_group_' + str(i + 1)
            g.investor_file = self.session.config[investors]
            g.jump_file = self.session.config[jumps]
            # g.json = {
            #     "messages": [],
            # }
            g.save()

        for p in players:
            p.default_fp = self.session.config['fundamental_price'] * 1e4
            p.spread = self.session.config['initial_spread'] * 1e4
            p.profit = self.session.config['initial_endowment'] * 1e4
            p.speed_cost = self.session.config['speed_cost'] * (1e+4) * (1e-9)
            p.save()

        self.session.save()

class Group(BaseGroup):

    exch_host = models.StringField()
    exch_port = models.IntegerField()
    investor_file = models.StringField()
    jump_file = models.StringField()

    def connect_to_exchange(self):
        log.info("Group%d: Connecting to exchange on port %d" % (self.id, self.exch_port))
        exchange.connect(self, self.exch_host, self.exch_port, wait_for_connection=True)
        log.info("Group%d: Connected to exchange on port %d" % (self.id, self.exch_port))

    def disconnect_from_exchange(self):
        exchange.disconnect(self, self.exch_host, self.exch_port)
        log.info("Group%d: Disconnected from exchange on port %d" % (self.id, self.exch_port))

    def send_exchange(self, msgs, delay=False, speed=False):
        if delay:
            dur = Constants.short_delay if speed else Constants.long_delay
            log.info('Group%d: Delaying order: %f.' % (self.id, dur))
        else:
            dur = 0.
        conn = exchange.connect(self, self.exch_host, self.exch_port).connection
        for m in msgs:
            conn.sendMessage(m, dur)

    def receive_from_exchange(self, msg):
        msg_format = (msg[0], len(msg))   # index 0 is message type     
        try: 
            ouch = translate.get_types()[msg_format](msg)
            if ouch['type'] == 'S':
                return
        except KeyError:
            msg_type ,msg_len = chr(msg[0]), len(msg)
            log.warning('Group{}: received type-{}:length-{}'.format(self.id, msg_type, msg_len))
        if ouch['order_token'][3] == '@':     # index 3 is subject ID
            if ouch['type'] == 'E':
                log.info('Group%d: Investor transacted.' % self.id)
            else:
                pass
        else:
            pid = ord(ouch['order_token'][3]) - 64
            player = self.get_player_by_id(pid)
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
        fires exogenous investors and jumps
        as subprocesses
        """
        log.info('Group%d: Fire %s.' % (self.id, name))
        cmd = ['python', name, str(self.id), url, data]
        subprocess.Popen(cmd)

    def jump_event(self, new_price):
        log.info('-----------Jump Start---------------')
        lablog = prepare(
            group=self.id, level='env', typ='jump', fp=new_price
        )
        log.experiment(lablog) 
        log.info('Group%d: Jump, new price is %d!' % (self.id, new_price) )

        # Check if group.id is the designated FPC updater
        if cache.get('profit_pusher') == self.id:
            # Push new profit to Price_Log
            fp_log = cache.get('FP_Log')
            fp_log.push(labtime(), new_price)
            cache.set('FP_Log', fp_log, timeout=None)
        # broadcast new price to clients
        self.broadcast(ClientMessage.fund_p_change(new_price))

        players = self.get_players()    # get all players
        player_responses = []
        fast_players = []
        slow_players = [] 

        for i, player in enumerate(players):
            response = player.jump(new_price)   # make them respond to jump
            player_responses.append(response['order'])
            if response['order']:   # participants in the market will create new orders
                if response['speed']: 
                    fast_players.append(i)
                else:
                    slow_players.append(i)      

        if fast_players:    # shuffle fast players' response and send to exchange
            random.shuffle(fast_players)
            fast_order = [i+1 for i in fast_players]
            log.info(
                'Group{}: fast players move order: {}'.format(self.id, fast_order)
            )
            for i in fast_players:
                state = players[i].state
                pid = players[i].id_in_group
                log.debug(
                    'Group%d: fast %s player%d moves.' % (self.id, state, pid )
                )
                self.send_exchange(player_responses[i], delay=True, speed=True)
        else:
            log.info('No fast players.')

        if slow_players:    # then shuffle and send slow players' response
            random.shuffle(slow_players)
            slow_order = [i+1 for i in slow_players]
            log.info(
                'Group{}: slow players move order: {}'.format(self.id, slow_order)
            )
            for i in slow_players:
                state = players[i].state
                pid = players[i].id_in_group
                log.debug(
                    'Group%d: slow %s player%d moves.' % (self.id, state, pid)
                )
                self.send_exchange(player_responses[i], delay=True, speed=False)
        else:
            log.info('No slow players')
                
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
    spread = models.IntegerField()
    channel = models.CharField(max_length=255)
 #  ready = models.BooleanField(initial=0)
    default_fp = models.IntegerField()
    profit = models.IntegerField(initial=200000)     
    time_of_speed_change = models.BigIntegerField()
    speed_cost = models.IntegerField()

    # Player actions

    def stage_enter(self, side, price=None, time_in_force=99999):
        """
        create an enter order
        default to maker enter order
        return the ouch message
        """  
        spread = (self.spread if side == 'S' else - self.spread)
        price = (int(self.fp() + spread / 2) if not price else price)
        order = self._create_order(
            status='stg', side=side, price=price, o_type='O', time_in_force=time_in_force
        )    
        ouch = translate.enter(order)
        log.info('Player%d: Stage: Enter %s: %s.' % (self.id, order.side, order.token))
        return ouch

    def stage_replace(self, order):
        """
        replace existing order
        create a new order 
        return a the ouch message
        """
        spread = (self.spread if order.side == 'S' else - self.spread)
        price = int(self.fp() + spread / 2)
        new_order = self._create_order(
            status='re', side=order.side, price=price, time_in_force=99999
        )
        orderstore = self.order_store()
        order_to_replace = orderstore.find_head(order)
        if not order_to_replace:
            return False
        order_to_replace.to_replace(labtime(), new_order.token)
        orderstore.active[order_to_replace.token] = order_to_replace
        ouch = translate.replace(order_to_replace, new_order)        
        self.save_order_store(orderstore)
        log.info(
            'Player%d: Stage: Replace: %s with %s.' % (self.id, order_to_replace.token, new_order.token)
        )
        return ouch


        # order_to_replace = self.find_head(order) 
        # spread = (self.spread if order_to_replace.side == 'S' else - self.spread)
        # price = int(self.fp() + spread / 2)
        # new_order = self._create_order(
        #     'replace', side=order_to_replace.side, price=price, time_in_force=99999
        # )
        # ouch = translate.replace(order_to_replace, new_order)
        # order_store = self.order_store()
        # order_store.register_replace(labtime(), order_to_replace, new_order.token)
        # self.save_order_store(order_store)
        # log.info(
        #     'Player%d: Stage: Replace: %s with %s.' % (self.id, order_to_replace.token, new_order.token)
        # )
        # return ouch

    def stage_cancel(self, order):
        """
        create a cancel order message
        return the ouch message
        """

        ouch = translate.cancel(order.token)
        log.info('Player%d: Stage: Cancel: %s.' % (self.id, order.token))
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
        log.debug('Player%d: Enters market.' % (self.id)) 
        msgs = [self.stage_enter('B'), self.stage_enter('S')]
        self.group.send_exchange(msgs, delay=True, speed=self.speed)

    def orders_in_market(self):
        orderstore = self.order_store()
        orders = list(orderstore.get_all('act').values())
        log.debug('Player%s: %d orders in market.' % (self.id, len(orders)))
        if len(orders) < 2:  # maker does not have 2 active orders in the market.
            staged_orders = list(orderstore.get_all('stg').values())
            log.debug('Player%s: %d orders staged.' % (self.id, len(staged_orders)))    
            orders.extend(staged_orders)
       # assert len(orders) == 2
        return orders

    def _leave_market(self):
        """
        exit market after switching from maker
        pass two ouch messages to cancel active orders
        """    
        orders = self.orders_in_market()
        if orders:
            msgs = [self.stage_cancel(o) for o in orders]
            self.group.send_exchange(msgs, delay=True, speed=self.speed)
        else:
            log.debug('Player%d: No active orders.' % self.id)
        self.group.broadcast(ClientMessage.spread_change(self.id_in_group))
    


    def makers_replace(self, flag):
        """
        implement makers' response to jumps and spread changes
        find active orders
        compose replace messages
        flag determines the side of spread to replace first
        return ouch messages
        """
        orders = self.orders_in_market()
        sorted_orders = sorted(  # better to start from above if jump is positive.
            orders, key=lambda order: order.price, reverse=flag
        )
        msgs = []
        for o in sorted_orders:
            m = self.stage_replace(o)
            if m is not False:
                msgs.append(m)
        return msgs

        # order_store  = self.order_store()
        # act_ords = order_store.get_active_set().values()    # active orders in the market
        # staged_enter_ords = order_store.get_staged_enter_set().values()
        # if act_ords:    
        #     sorted_ords = sorted(  # have to start from above if jump is positive
        #         ords, key=lambda order: order.price, reverse=flag
        #     )
        #     msgs = [self.stage_replace(o) for o in sorted_ords]   # replace messages for active orders
        # if staged_enter_orders
        #     staged_ords = 
        #     try:
        #         log.debug('Player%s: Replacing staged orders.' % self.id)
        #         sorted_ords = sorted(
        #             staged_ords, key=lambda order: order.price, reverse=flag
        #             )
        #         msgs = [self.stage_replace(o) for o in sorted_ords]
        #         return msgs
        #     except TypeError:
        #         err =  ('Player%s: A maker without any active/staged orders.' % self.id )
        #         raise Exception(err)
   
    # Client actions

    def update_state(self, message):
        """
        switch between 3 roles (states): out, sniper and maker
        """
        states = {
            'OUT':self._leave_market,
            'SNIPER':self._leave_market,
            'MAKER':self._enter_market
        }
        new_state = message['state']
        self.state = new_state
        self.save() 
        log.info('Player%d: State is now: %s.' % (self.id, self.state))    
        log.debug('Player%d: Start state update.' % (self.id)) 
        try:
            states[new_state]()
        except KeyError:    # like this is possible
            log.info('Player%d: Invalid state update.' % self.id)
        lablog = prepare(
            group=self.group_id, level='choice', typ='state', 
            pid=self.id_in_group, nstate=self.state
        )
        log.experiment(lablog) 
        
           
    def update_spread(self, message):
        """
        makers can change their spreads
        read new spread 
        let all clients know
        replace existing orders with new price
        """
        new_spread = int(message['spread']) 
        log.debug('Player%d: Start spread update: %s.' % (self.id, new_spread))
        self.spread = new_spread 
        # fp  = self.fp()  # what is my fundamental price ?
        # lo, hi = fp - self.spread / 2, fp + self.spread / 2  # then these are legs
        # self.group.broadcast(
        #     ClientMessage.spread_change(self.id_in_group, leg_up=hi, leg_low=lo)
        # )
        msgs = self.makers_replace(1)  # replace orders, start from above
        self.group.send_exchange(msgs, delay=True, speed=self.speed)
        self.save()
        log.info('Player%d: Spread update: %s.' % (self.id, self.spread))
        lablog = prepare(
            group = self.group_id, level='choice', typ='spread', 
            pid=self.id_in_group, nspread=self.spread
        )
        log.experiment(lablog) 

        # active_ords = self.order_store().get_active_set().values()
        # log.debug('Player%d: Start spread change.' % (self.id)) 
        # if active_ords:
        #     log.debug('Player%d: Replace active orders.' % (self.id)) 
        #     msgs = [self.stage_replace(o) for o in active_ords]
        # else:
        #     log.debug('Player%s: Replace staged orders.' % self.id)
        #     order_store = self.order_store()
        #     staged_ords = order_store.get_staged_enter_set().values()
        #     msgs = [self.stage_replace(o) for o in staged_ords]

    def update_speed(self, message): 
        """
        switch between slow and fast
        calculate cost if player turns off speed
        record time if player turns on speed
        """  
        self.speed = not self.speed
        self.save()
        speed = 'fast' if self.speed else 'slow'
        log.info('Player%d: Speed change: %s.' % (self.id, speed))
        now = labtime()
        if self.speed:
            self.time_of_speed_change = now
        else:
            self._calc_speed_cost(now)
        self.save()
        lablog = prepare(
            group=self.group_id, level='choice', typ='speed', 
            pid=self.id_in_group, nspeed=self.speed
        )
        log.experiment(lablog) 

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
        order = orderstore.get_order(tok)
        assert order    # I should get rid of these asserts after testing
        orderstore.activate(stamp, order)
        orderstore.active[order.token] = order
        log.info('Player%d: Confirm: Enter: %s.' % (self.id, tok))
        self.save_order_store(orderstore)
        if self.state == 'MAKER':
            fp  = self.fp()  # what is my fundamental price ?
            lo, hi = fp - self.spread / 2, fp + self.spread / 2  # then these are legs
            self.group.broadcast(
                ClientMessage.spread_change(self.id_in_group, leg_up=hi, leg_low=lo)
            )
        lablog = prepare(
            group = self.group_id, level='exch', typ='enter', 
            pid= self.id_in_group, token= order.token, stamp= order.timestamp, 
            side= order.side, tif= order.time_in_force, price=order.price
        )
        log.experiment(lablog)

    def confirm_replace(self, msg):
        """
        handle replaced messages for the player 
        """
        ptok, tok = msg['previous_order_token'], msg['order_token']
        stamp = msg['timestamp']
        orderstore = self.order_store()
        old_order = orderstore.get_order(ptok)
        assert old_order
        new_order = orderstore.get_order(tok)
        assert new_order
        orderstore.cancel(stamp, old_order)
        orderstore.activate(stamp, new_order)
        orderstore.active[new_order.token] = new_order
        orderstore.inactive[old_order.token] = old_order
        self.save_order_store(orderstore)
        if self.state == 'MAKER':
            fp  = self.fp()
            lo, hi = fp - self.spread / 2, fp + self.spread / 2
            self.group.broadcast(
                ClientMessage.spread_change(self.id_in_group, leg_up=hi, leg_low=lo)
            )
        log.info('Player%d: Confirm: Replace %s with %s.' % (self.id, ptok, tok))
        lablog = prepare(
            group = self.group_id, level='exch', typ='replace', 
            pid=self.id_in_group, old_token=old_order.token, new_token=new_order.token, stamp=new_order.timestamp,
        )
        log.experiment(lablog)

    def confirm_cancel(self, msg):
        """
        handles canceled messages
        find canceled order in the order store
        move it to inactive dict
        update order state as canceled
        """
        stamp, tok = msg['timestamp'], msg['order_token']
        orderstore = self.order_store()
        order = orderstore.get_order(tok)
        assert order
        orderstore.cancel(stamp, order)
        self.save_order_store(orderstore)        
        log.info('Player%d: Confirm: Cancel %s.' % (self.id, tok))
        lablog = prepare(
            group = self.group_id ,level='exch', typ='cancel', 
            pid= self.id_in_group, token= order.token, stamp=order.timestamp
        )
        log.experiment(lablog)

    def confirm_exec(self,msg):
        """
        handles execution messages
        update order state as executed
        take profit
        """
        stamp, tok = msg['timestamp'], msg['order_token']
        price = msg['price']
        orderstore = self.order_store()
        order = orderstore.get_order(tok)
        orderstore.execute(stamp, order)
        self.save_order_store(orderstore) 
        log.info('Player%d: Confirm: Transaction: %s.' % (self.id, tok))
        profit = self.calc_profit(price, order.side, stamp) 
        log.info('Player%d: Take Transaction Profit: %d.' % (self.id, profit))
        self.group.broadcast(
            ClientMessage.execution(self.id_in_group, tok, profit)
        )
        if self.state == 'MAKER':
             log.debug('Player%d: Execution action: Enter a new order.' % self.id)
             m = [self.stage_enter(order.side)]
             self.group.send_exchange(m, delay=True, speed=self.speed)
        lablog = prepare(
            group=self.group_id , level='exch', typ= 'exec', 
            pid=self.id_in_group, token=order.token, price=order.price, stamp=order.timestamp
        )
        log.experiment(lablog)

    def calc_profit(self, exec_price, side, timestamp):
        """
        find the distance btw fundamental and execution prices
        order side determines profit sign
        take speed cost along the way
        """
        fp = cache.get('FP_Log').getFP(timestamp)

        d = abs(fp - exec_price)
        if exec_price < fp:
            pi = d if side == 'B' else -d  # buyer (seller) buys (sells) less than fp
        else:
            pi = d if side == 'S' else -d  # seller (buyer) sells (buys) higher than fp 
        self.profit += pi
        if self.speed:
            self._calc_speed_cost(labtime())
        self.save()
        lablog = prepare(
            group=self.group_id, level='market', typ='profit', 
            source='cross', pid=self.id_in_group, stamp=timestamp,
            endowment=self.profit, profit=pi 
        )
        log.experiment(lablog)
        return pi
    
    def _calc_speed_cost(self, timestamp):
        """
        calculate speed cost since the previous calculation
        """
        delta = timestamp - self.time_of_speed_change
        cost = delta * self.speed_cost
        self.time_of_speed_change = timestamp
        self.profit -= cost
        log.info('Player%d: Take speed cost: %d' % (self.id, cost))
        lablog = prepare(
            group=self.group_id, level='market', typ='profit', 
            source='speed', pid=self.id_in_group, stamp=timestamp,
            endowment= self.profit, profit=-cost 
        )
        log.experiment(lablog)

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
        """
        player's response to jump
        update fundamental price
        return jump response to group.jump
        """
        is_positive = new_price - self.fp() > 0.
        self.fp_update(new_price)
        response = {'order': False, 'speed': self.speed}
        current_role = self.state

        if current_role == 'SNIPER':
            log.debug('Player%d: Jump Action: Snipe.' % self.id)
            side = 'B' if is_positive else 'S'
            order = [self.stage_enter(side, price=self.fp(), time_in_force=0)]
            response['order'] = order
        elif current_role == 'MAKER':
            log.debug('Player%d: Jump Action: Replace orders.' % self.id)
            flag = 1 if is_positive else 0
            orders = self.makers_replace(flag)
            response['order'] = orders
        else:
            log.debug('Player%d: Jump Action: Nothing to do.' % self.id)
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

    """
    send message to the client after an event
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
        k = str(self.id) + '_orders'
        order_store = cache.get(k)
        if not order_store:
            log.info('Player%d: Create Order Store.' % self.id)
            order_store = OrderStore(self.id, self.id_in_group)
            cache.set(k, order_store, timeout=None)
        return order_store

    def save_order_store(self, orderstore):
        """
        write to cache
        """
        k = str(self.id) + '_orders'
        cache.set(k, orderstore, timeout=None)

    def fp(self):
        """
        each player stores a fundamental price on cache
        read from cache
        return fp
        """
        k = str(self.id) + '_fp'
        fp = cache.get(k)
        if not fp:
            fp = self.default_fp
            log.info(
                'Player%d: Define fundamental price as %d .' % (self.id, fp)
            )
            cache.set(k, fp, timeout=None)
        return fp

    def fp_update(self, new_fp):
        k = str(self.id) + '_fp'
        cache.set(k, new_fp, timeout=None)
        log.info('Player%d: Update FP: %d' % (self.id, new_fp))

        



class Investor(Model):

    group = ForeignKey(Group)
    order_count = models.IntegerField(initial=1)

    def receive_from_consumer(self, side):
        s = ('Buy' if side=='B' else 'Sell')
        log.info('Investor%d: %s.' % (self.order_count, s))
        self.invest(side)

    def invest(self, side):
        p = (2147483647 if side == 'B' else 0)
        order = Order(0, self.order_count, status='s', side=side, price=p, time_in_force=0)
        ouch = translate.enter(order)
        log.debug('Investor sends an order: %s' % order.token)
        self.group.send_exchange([ouch])
        self.order_count += 1
        self.save()
