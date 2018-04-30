from .translator import *
from .utility import Get_Time
import numpy as np
from otree.db.models import Model, ForeignKey
from django.core import serializers
import time
import pandas as pd
try:
    import thread
except ImportError:
    import _thread as thread
from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
from jsonfield import JSONField
#from . import exchange_server
import subprocess
import os
import logging

logger = logging.getLogger(__name__)

author = 'LEEPS Lab UCSC'

doc = """
Your app description
"""


class Constants(BaseConstants):
    name_in_url = 'oTree_HFT_CDA'
    players_per_group = 2
    num_rounds = 5

    # exchange_soc = Exchange_Socket()

    inv_py = './oTree_HFT_CDA/investor.py'
    inv_url = 'ws://127.0.0.1:8000/hft_investor/'   
    inv_csv = './oTree_HFT_CDA/investor_test.csv'

    jump_py = './oTree_HFT_CDA/jump.py'
    jump_url = 'ws://127.0.0.1:8000/hft_jump/'
    jump_csv = './oTree_HFT_CDA/jump_test.csv'


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):

    def spawn(self, name, url, data):
        log = 'Group %d: Initialize %s..' % (self.id, name)
        logging.info(log)
        cmd = ['python', name, str(self.id), url, data]
        subprocess.Popen(cmd)

    def jump_event(self, new_price):
        log = 'Jump to %d!' % new_price
        logging.info(log)
        """
        delay and jump players here
        """

    def send_to_exchange(self, message, wait_time):
        # james, this is called by the players
        # a probability model is applied, then a wait logic
        # is executed.

        # Then we need to call some function to send the message
        # to the exchange
        pass

    def receive_from_exchange(self, message, wait_time):
        # this function is called by the twisted threads to
        # decode the binary and send to the correct player

        decoded = chr(exchange_msg[0])

        #call correct translator method and pass to player


class Player(BasePlayer):

    # basic state variables
    state = models.StringField(initial='OUT')
    speed = models.BooleanField(initial=0)  # 0 or 1
    spread = models.IntegerField(initial=2)
    channel = models.StringField()
    # fundamental price
    fp = models.IntegerField(initial=10)
    order_count = models.IntegerField(initial=1)

    # Staging orders

    def stage_enter(self, side):
        spread = self.spread
        if side == 'B': spread = - spread
        order = self.order_set.create(side=side,
                                      price=self.fp + spread / 2,
                                      o_type='O',
                                      time_in_force=99999)
        order.stage()
        ouch = Enter_Order_Msg(order)
        # send_to_exchange(ouch)
        log = 'Player %d: Stage enter %s order.' % (self.id_in_group, order.side) 
        logging.info(log)
        logging.info(order)

    def stage_replace(self, order):
        spread = self.spread
        if order.side == 'B': spread = - spread
        price = self.fp + spread / 2
        order.stage_update('R', price)
        # create the new order
        new_order = self.order_set.create(side=order.side, price=price)
        new_order.save()
        ouch = Replace_Order_Msg(order, new_order)
        # send_to_exchange(ouch)
        log = 'Player %d: Stage replace order %s.' % (self.id_in_group, order.token)
        logging.info(log)
        logging.info(order)   

    def stage_cancel(self, order):
        order.stage_update('C')
        ouch = Cancel_Order_Msg(order.token)
        # send_to_exchange(ouch)
        log = 'Player %d: Stage cancel for the order %s.' % (self.id_in_group, order.token)
        logging.info(log)
        logging.info(order)

    # Player actions

    def leave_market(self):
        ords = self.order_set.filter(status=['A'])
        if len(ords) > 0:
            for o in ords:
                self.stage_cancel(o)
        else:
            log = 'Player %d has no active orders.' % self.id_in_group
            logging.info(log)

    def update_state(self, new_state):
        if new_state == 'OUT':
            self.leave_market()
        elif new_state == 'SNIPER':
            self.leave_market()
        elif new_state == 'MAKER':  # Player enters as a maker
            self.stage_enter(side='B')   # Spread ? default or most recent ?
            self.stage_enter(side='S')
        else:
            log = 'Player %d: Invalid state update.' % self.id_in_group
            logging.warning(log)
        self.state = new_state
        log = 'Player %d is %s.' % (self.id_in_group, self.state)
        logging.info(log)

    def update_price(self, new_spread=None):
        if new_spread:
            self.spread = new_spread
        ords = player.order_set.filter(status__in=['A'])
        if len(ords) > 0:
            for o in ords:
                self.stage_replace(o)
        else:
            log = 'Player %d: No active orders.' % self.id_in_group
            logging.info(log)

    def update_speed(self):
        self.speed = not self.speed

    # Receive methods

    def receive_from_client(self, message):
        if message['type'] == 'role_change':
            self.update_state(message['state'])
        elif message['type'] == 'spread_change':
            self.update_spread(message['spread'])
        elif message['type'] == 'speed_change':
            self.update_speed()
        else:
            raise Exception('Bad message type received from client.')

    def receive_from_group(self, message):
        if message['type'] == 'A':
            confirm_enter(message)
        elif message['type'] == 'U':
            confirm_replace(message)
        elif message['type'] == 'C':
            confirm_cancel(message)
        elif message['type'] == 'E':
            confirm_enter(message)
        else:
            raise Exception('Bad message type received from exchange.')

    # Confirm when receive from exchange        
    # These methods should send response to clients ! 
    def confirm_enter(self,message):
        order = self.order_set.get(token=message['order_token'])
        order.activate(message['timestamp'])
        log = 'Player %d: Confirmed %s, %s.' % (self.id_in_group, order.token)
        logging.info(log)

    def confirm_replace(self, message):
        previous_ord_token = message['existing_order_token']
        replacement_ord_token = message['order_token']
        old_order = self.order_set.get(token=previous_ord_token)
        new_order = self.order_set.get(token=replacement_ord_token)
        old_order.cancel(message['timestamp'])
        new_order.activate(message['timestamp'])
        log = 'Player %d: Confirmed replace %s, %s.' % (self.id_in_group, order.token)
        logging.info(log)

    def confirm_cancel(self, message):
        ord_token = message['order_token']
        order = self.order_set.get(token=ord_token)
        order.cancel(message['timestamp'])
        log = ( 'Player %d: Confirmed cancel %s, was a %s.' 
            % (self.id_in_group, order.token, order.side))
        logging.info(log)

    def confirm_exec(self,message):
        order_token = message['order_token']
        order = self.order_set.get(token=order_token)
        order.execute(message['timestamp'])
        log = ('Player %d: Confirmed transaction %s, %s is a %s.' 
            % (self.id_in_group, order.token, order.side))
        logging.info(log)
        self.stage_enter(order.side)

    def jump_event(self, new_price):   # ! delays to be handled at group level
        old_fp = self.fp              # ! snipes itself ?  
        self.fp = new_price

        postive_jump = (self.fp - old_fp) > 0

        if self.state == 'OUT':
            return
        elif self.state == 'SNIPER':
            if postive_jump:
                self.stage_enter(side='B', price=2147483647)  # Special value for a market order
            else:
                self.stage_enter(side='S', price=2147483647)  # Special value for a market order
        else:
            self.update_price()


class Investor(Model):

    group = ForeignKey(Group)

    def receive_from_consumer(self, side):
        now = str(Get_Time())
        logging.info('Investor arrives. : ' + side + ' ' + now)
        self.go_market(side)


    def go_market(self, side):
        """
        create ouch message here 
        side = side, price = 2147483647
        """
        pass

    # receives confirmation ? 


class Order(Model):
    # NASDAQ ouch fields
    o_type = models.StringField(initial=None)
    token = models.StringField()  # DAN
    side = models.StringField(initial=None)
    shares = models.IntegerField(initial=1)
    stock_sym1 = models.IntegerField(initial=1280332576)
    stock_sym2 = models.IntegerField(initial=538976288)
    price = models.IntegerField(initial=None)
    time_in_force = models.IntegerField(initial=None)
    firm = models.StringField(initial=None)
    display = models.StringField(initial='Y')
    capacity = models.StringField(initial='P')
    iso = models.StringField(initial='N') # intermarket sweep eligibility
    min_quantity = models.IntegerField(initial=0)
    cross_type = models.StringField(initial='N')
    customer_type = models.StringField(initial='R')

    # otree fields
    time_stage = models.IntegerField()
    timestamp = models.IntegerField(initial=None)
    status = models.StringField(initial='S')
    update_staged = models.StringField(initial=None)
    time_canceled = models.IntegerField(initial=None)
    player = ForeignKey(Player)
#   last_replaced = models.StringField(initial=None)   # Also maybe redundant

    def stage(self):
        time = Get_Time(granularity="nanoseconds")
        self.time_stage = time
        self.token = "SUB" + str(chr(self.player.id_in_group + 64)) + str(self.side) + str(format(self.player.order_count, '09d'))
        self.firm = "SUB" + str(chr(self.player.id_in_group + 64))
        self.player.order_count += 1
        self.save()

    def activate(self, time):
        self.status = 'A'
        self.timestamp = time
        self.save()

    def cancel(self, time):
        self.status = 'C'
        self.time_canceled = time
        self.save()

    def execute(self, time):
        self.status = 'X'
        self.timestamp = time
        self.save()

    def stage_update(self, type, price=None):
        time = Get_Time(granularity="nanoseconds")
        update = str(time) + ' ' + type
        if price:
            update.join(' ' + str(price))
        self.update_staged = update
        self.save()

    def __str__(self):
        time_to_print = self.timestamp if self.timestamp else self.time_stage
        out =  (
                str(time_to_print) + ' ' + self.side + ' ' +
                str(self.price) + ' ' +  self.status + '\n'
                )
        if self.update_staged:
            rest = '\t'  + 'UPDATE: ' +  update_staged
            out = out.join(rest)
        return out

    def order_export(self):
        data = serializers.serialize("json", Order.objects.all())
        df = pd.read_json(data)
        df.to_csv('Orders.csv')

