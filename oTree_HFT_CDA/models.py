from .translator import *
from .utility import Get_Time

from . import exchange

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
    def creating_session(self):
        for i, group in enumerate(self.get_groups()):
            group.port = 9000 + i + 1
            group.json = {
                "messages": [],
            }
            group.save()


class Group(BaseGroup):
    port = models.IntegerField()
    json = JSONField()

    def connect_to_exchange(self):
        print("Connecting to exchange on port %d", self.port)
        exchange.connect(self, '127.0.0.1', self.port)
        print("Connected to exchange on port %d", self.port)

    def disconnect_from_exchange(self):
        exchange.disconnect(self, '127.0.0.1', self.port)

    def send_message_delay(self, msgs, speed):
        if speed is True:
            time.sleep(0.1)
        elif speed is False:
            time.sleep(0.5)
        conn = exchange.connect(self, '127.0.0.1', self.port, wait_for_connection=True).connection
        for m in msgs:
            conn.sendMessage(m)

    def send_message_nondelay(self, msg):
        conn = exchange.connect(self, '127.0.0.1', self.port, wait_for_connection=True).connection
        conn.sendMessage(msg)



    def recv_message(self, msg):
        ouch_msg = {}
        if(msg[0] == ord('S') and len(msg) == 10):
            ouch_msg = System_Event_Message(msg)
            print(ouch_msg)
            # send broadcast to start playing
            return
        elif(msg[0] == ord('E') and len(msg) == 49):
            ouch_msg = Executed_Message(msg)
            print(ouch_msg)
        elif(msg[0] == ord('C') and len(msg) == 28):
            ouch_msg = Canceled_Message(msg)
            print(ouch_msg)
        elif(msg[0] == ord('U') and len(msg) == 80):
            ouch_msg = Replaced_Message(msg)
            print(ouch_msg)
        elif(msg[0] == ord('A') and len(msg) == 66):
            ouch_msg = Accepted_Message(msg)
            print(ouch_msg)
        else:
            logging.info("Received Message from with msg type {} and length {}".format(chr(msg[0]), len(msg)))
        

        player = self.get_player_by_id(ord(ouch_msg['order_token'][3]) - 64)
        player.receive_from_group(ouch_msg)


        self.json['messages'].append(ouch_msg)
        self.save()

    def save(self, *args, **kwargs):
        """
        BUG: Django save-the-change, which all oTree models inherit from,
        doesn't recognize changes to JSONField properties. So saving the model
        won't trigger a database save. This is a hack, but fixes it so any
        JSONFields get updated every save. oTree uses a forked version of
        save-the-change so a good alternative might be to fix that to recognize
        JSONFields (diff them at save time, maybe?).
        """
        super().save(*args, **kwargs)
        if self.pk is not None:
            json_fields = {}
            for field in self._meta.get_fields():
                if isinstance(field, JSONField):
                    json_fields[field.attname] = getattr(self, field.attname)
            self.__class__._default_manager.filter(pk=self.pk).update(**json_fields)


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


        log = 'Player %d: Stage enter %s order.' % (self.id_in_group, order.side) 
        logging.info(log)
        logging.info(order)
        return list(ouch)

    def stage_replace(self, order):
        spread = self.spread
        if order.side == 'B': spread = - spread
        price = self.fp + spread / 2
        order.stage_update('R', price)
        # create the new order
        new_order = self.order_set.create(side=order.side, price=price)
        new_order.save()
        ouch = Replace_Order_Msg(order, new_order)
    
        log = 'Player %d: Stage replace order %s.' % (self.id_in_group, order.token)
        logging.info(log)
        logging.info(order)   

        return ouch

    def stage_cancel(self, order):
        order.stage_update('C')
        ouch = Cancel_Order_Msg(order.token)
        
        # self.group.send_message_delay(ouch, self.speed)

        log = 'Player %d: Stage cancel for the order %s.' % (self.id_in_group, order.token)
        logging.info(log)
        logging.info(order)

        return ouch

    # Player actions

    def leave_market(self):
        ords = self.order_set.filter(status=['A'])
        print(ords)
        if len(ords) > 0:
            msgs = []
            for o in ords:
                msgs.append(self.stage_cancel(o))
            return msgs
        else:
            log = 'Player %d has no active orders.' % self.id_in_group
            logging.info(log)

    def update_state(self, new_state):
        if new_state == 'OUT':
            m = self.leave_market()
            self.group.send_message_delay(m, self.speed)
        elif new_state == 'SNIPER':
            m = self.leave_market()
            self.group.send_message_delay(m, self.speed)
            # is there supposed to be action here?
        elif new_state == 'MAKER':  # Player enters as a maker
            m = self.stage_enter(side='B') + self.stage_enter(side='S')
            self.group.send_message_delay(m, self.speed)

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
            msgs = []
            for o in ords:
                msgs.append(self.stage_replace(o))
            self.group.send_message_delay(msgs, self.speed)
        else:
            log = 'Player %d: No active orders.' % self.id_in_group
            logging.info(log)


    def update_speed(self):  
        self.speed = not self.speed      # Front end button doesnt work 0429
        speed = 'fast' if self.speed else 'slow'
        log = 'Player %d is %s.' % (self.id_in_group, speed)
        logging.info(log)

    # Receive methods

    def receive_from_client(self, message):
        if message['type'] == 'role_change':
            self.update_state(message['state'])
        elif message['type'] == 'spread_change':
            self.update_price(message['spread'])
        elif message['type'] == 'speed_change':
            self.update_speed()
        else:
            raise Exception('Bad message type received from client.')

    def receive_from_group(self, message):
        if message['type'] == 'A':
            self.confirm_enter(message)
        elif message['type'] == 'U':
            self.confirm_replace(message)
        elif message['type'] == 'C':
            self.confirm_cancel(message)
        elif message['type'] == 'E':
            self.confirm_exec(message)
        else:
            raise Exception('Bad message type received from exchange.')

    # Confirm when receive from exchange        
    # These methods should send response to clients ! 
    def confirm_enter(self,message):
        order = self.order_set.get(token=message['order_token'])
        order.activate(message['timestamp'])
        log = 'Player %d: Confirmed %s.' % (self.id_in_group, order.token)
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

