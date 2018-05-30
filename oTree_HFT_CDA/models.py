#!/usr/bin/env python
import subprocess
import os
import logging
import random
import time
import pandas as pd
from . import translator as translate
from .utility import nanoseconds_since_midnight, tokengen, Get_Time
from . import exchange
from .profit import Price_Log, Price_Node
from channels import Group as CGroup, Channel
from otree.db.models import Model, ForeignKey
from django.core import serializers
from otree.api import (
    models, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
)
from jsonfield import JSONField
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
    players_per_group = 2
    num_rounds = 1
    speed_cost = 0.1

    inv_py = os.path.join(os.getcwd(), 'oTree_HFT_CDA/exos/investor.py')
    inv_url = 'ws://127.0.0.1:8000/hft_investor/'   
    inv_csv = os.path.join(os.getcwd(), 'raw/inv_test.csv')

    jump_py = os.path.join(os.getcwd(), 'oTree_HFT_CDA/exos/jump.py')
    jump_url = 'ws://127.0.0.1:8000/hft_jump/'   
    jump_csv = os.path.join(os.getcwd(), 'raw/jump_test.csv')




class Subsession(BaseSubsession):
    
    def creating_session(self):
        # location of Price_Log object
        cache.set('FP_Log' , Price_Log(10), timeout=None)

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
        msg_type = (msg[0], len(msg))
        try: 
            ouch = translate.get_types()[msg_type](msg)
            if ouch['type'] == 'S':
                return
        except KeyError:
            log.warning('Group{}: received type-{}:length-{}'.format(self.id, chr(msg[0]), len(msg)))
        if (ouch['order_token'][3] == '@'):
            if ouch['type'] == 'E':
                log.info('Group%d: Investor transacted.' % self.id)
                note = {'note':'Something about the transaction.'}
                self.broadcast(note)
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
            fp_log.push(Get_Time('nanoseconds'), new_price)
            cache.set('FP_Log', fp_log, timeout=None)

        self.broadcast({"FPC":new_price})

        players = self.get_players()
        player_responses = []
        fast_players = []
        slow_players = [] 

        for i, player in enumerate(players):
            response = player.jump(new_price)
            player_responses.append(response[0])
            if response[0] is not None:
                if response[1]:
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

    # fundamental price
    fp = models.IntegerField(initial=10000)
    order_count = models.IntegerField(initial=1)
    profit = models.IntegerField(initial=10000)

    # Player actions

    def stage_enter(self, side, price=None, time_in_force=99999):
        """
        player creates one enter order
        defaults to maker enter order
        returns an ouch message
        """  
        spread = (self.spread if side == 'S' else - self.spread)
        price = (int(self.fp + spread / 2) if not price else price)
        order = self._create_order(side=side, price=price, o_type='O', time_in_force=time_in_force)    
        ouch = translate.enter(order)
        log.info('Player%d: Stage: Enter %s: %s.' % (self.id_in_group, order.side, order.token))
        return ouch

    def stage_replace(self, order):
        """
        player replaces existing order
        creates one new order 
        returns an ouch message
        """
        spread = (self.spread if order.side == 'S' else - self.spread)
        price = int(self.fp + spread / 2)
        new_order = self._create_order(side=order.side, price=price, time_in_force=99999)
        ouch = translate.replace(order, new_order)   
        log.info('Player%d: Stage: Replace: %s.' % (self.id_in_group, order.token))
        return ouch

    def stage_cancel(self, order):
        """
        player creates a cancel order message
        returns an ouch message
        """
        ouch = translate.cancel(order.token)
        log.info('Player%d: Stage: Cancel: %s.' % (self.id_in_group, order.token))
        return ouch

    def _create_order(self, **kwargs):
        """
        creates a new order in player's order store 
        this saves order store back in cache
        """
        orderstore = self.order_store()
        order = orderstore.create(**kwargs)
        self.save_order_store(orderstore)
        return order

    def _enter_market(self):
        """
        player enters market after switching role to maker
        passes two ouch messages to group
        """
        log.debug('Player%d: Enters market.' % (self.id_in_group)) 
        msgs = [self.stage_enter('B'), self.stage_enter('S')]
        self.group.send_exchange(msgs, delay=True, speed=self.speed)

    def _leave_market(self):
        """
        player exits market after switching from maker
        passes ouch messages to group to cancel active orders
        """
        ords = self.order_store().get_active_set().values()
        if ords:
            msgs = [self.stage_cancel(o) for o in ords]
            self.group.send_exchange(msgs, delay=True, speed=self.speed)
        else:
            log.debug('Player%d: No active orders.' % self.id_in_group)
   

    # Client actions
    def update_state(self, message):
        """
        clients can switch between 3 roles (states): OUT, SNIPER and MAKER
        """
        states = {
            'OUT':self._leave_market,
            'SNIPER':self._leave_market,
            'MAKER':self._enter_market
        }
        new_state = message['state']
        try:
            states[new_state]()
        except KeyError:    # like this is possible
            log.info('Player%d: Invalid state update.' % self.id_in_group)             
        self.state = new_state   
        self.save()
        log.info('Player%d: State update: %s.' % (self.id_in_group, self.state)) 


    def update_spread(self, message):
        """
        makers can update their spreads
        """
        self.spread = 2000*float(message['spread'])
        ords = self.order_store().get_active_set().values()
        if ords:
            msgs = [self.stage_replace(o) for o in ords]
            self.group.send_exchange(msgs, delay=True, speed=self.speed)
        self.save()
        log.info('Player%d: Spread update: %s.' % (self.id_in_group, self.spread))

    def update_speed(self, message): 
        """
        clients can switch between slow and fast.
        """  
        self.speed = not self.speed
        self.save()
        speed = ('fast' if self.speed else 'slow')
        log.info('Player%d: Speed change: %s.' % (self.id_in_group, speed))
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
        handles accept messages for the player
        """
        stamp, tok = msg['timestamp'], msg['order_token']
        orderstore = self.order_store()
        order = orderstore.get_staged(tok)
        assert order    # I should get rid of these asserts after testing
        orderstore.activate(stamp, order)
        log.info('Player%d: Confirm: Enter: %s.' % (self.id_in_group, tok))
        self.send_client({"Yo":"Mama"})
        self.save_order_store(orderstore)

    def confirm_replace(self, msg):
        """
        handles replaced messages for the player
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
        moves it to inactive dict
        updates order state as canceled
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
        finds executed order in the order store
        moves it to inactive dict
        updates order state as executed
        """
        stamp, tok = msg['timestamp'], msg['order_token']
        orderstore = self.order_store()
        order = orderstore.get_active(tok)
        orderstore.execute(stamp, order)
        self.save_order_store(orderstore) 
        log.info('Player%d: Confirm: Transaction: %s.' % (self.id_in_group, tok))
        # calc_profit(order.price, order.side)    # Uncomment for profit testing
        if self.state == 'MAKER':
             log.debug('Player%d: Execution action: Enter a new order.' % self.id_in_group)
             m = [self.stage_enter(order.side)]
             self.group.send_exchange(m, delay=True, speed=self.speed)

    def calc_profit(self, exec_price, side, timestamp):
        profit = 0
        fp = cache.get['FP_Log'].getFP(timestamp)

        if side == 'B':
            # Execution of your buy offer
            if exec_price < fp:     #  Player bought lower than FP (positive profit)
                profit += abs(fp - exec_price)  
            else:       #  Player bought higher than FP (negative profit)   
                profit -= abs(fp - exec_price)   
        else:
            # Execution of your sell offer
            if exec_price < fp:     #  Player sold lower than FP (negative profit)
                profit -= abs(fp - exec_price)    
            else:        #  Player sold higher than FP (positive profit)
                profit += abs(fp - exec_price)     

        self.profit += profit
        self.save()


    def jump(self, new_price):  
        old_fp = self.fp              
        self.fp = new_price
        self.save()
        postive_jump = (self.fp - old_fp) > 0

        if self.state == 'OUT':
            log.debug('Player%d: Jump Action: Nothing to do.' % self.id_in_group)
            return [None, self.speed]

        elif self.state == 'SNIPER':
            log.debug('Player%d: Jump Action: Snipe.' % self.id_in_group)
            side = ('B' if postive_jump else 'S')
            order = [self.stage_enter(side, price=self.fp, time_in_force=0)]
            return [order, self.speed]

        else:
            log.debug('Player%d: Jump Action: Replace orders.' % self.id_in_group)
            flag = (1 if postive_jump else 0)
            orders = self._adjust_price(flag)
            return [orders, self.speed]

    def _adjust_price(self, flag):
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
            log.info('Player%d: Create Order Store.' % self.id)
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