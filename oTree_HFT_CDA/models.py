import subprocess
import os
import logging
import random
import time
import pandas as pd
from . import translator as translate
from .utility import Get_Time, tokengen
from . import exchange
from channels import Group as CGroup, Channel
from otree.db.models import Model, ForeignKey
from django.core import serializers
from otree.api import (
    models, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
)
from jsonfield import JSONField

log = logging.getLogger(__name__)


author = 'LEEPS Lab UCSC'

doc = """
Your app description
"""


class Constants(BaseConstants):
    name_in_url = 'oTree_HFT_CDA'
    players_per_group = 2
    num_rounds = 5

    inv_py = os.path.join(os.getcwd(), 'oTree_HFT_CDA/exos/investor.py')
    inv_url = 'ws://127.0.0.1:8000/hft_investor/'   
    inv_csv = os.path.join(os.getcwd(), 'raw/inv_test.csv')

    jump_py = os.path.join(os.getcwd(), 'oTree_HFT_CDA/exos/jump.py')
    jump_url = 'ws://127.0.0.1:8000/hft_jump/'   
    jump_csv = os.path.join(os.getcwd(), 'raw/jump_test.csv')




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
        log.info("Group%d: Connecting to exchange on port %d" % (self.id, self.port))
        exchange.connect(self, '127.0.0.1', self.port)
        log.info("Group%d: Connected to exchange on port %d" % (self.id, self.port))

    def disconnect_from_exchange(self):
        exchange.disconnect(self, '127.0.0.1', self.port)
        log.info("Group%d: Disconnected from exchange on port %d" % (self.id, self.port))

    def send_exchange(self, msgs, delay=False, speed=False):
        if delay:
            dur = (0.1 if speed else 0.5)
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

        self.json['messages'].append(ouch)
        self.save()

    def broadcast(self, note):
        log.debug('Group%d: Broadcast investor transaction.' % self.id)
        CGroup(str(self.id)).send(note)


    def save(self, *args, **kwargs):
        """
        JAMES
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
        log.info('Group%d: Fire %s.' % (self.id, name))
        cmd = ['python', name, str(self.id), url, data]
        subprocess.Popen(cmd)

    def jump_event(self, new_price):
        log.info('Group%d: Jump, new price is %d!' % (self.id, new_price))

        players = self.get_players()
        player_responses = []
        fast_players = []
        slow_players = [] 

        for i, player in enumerate(players):
            response = player.jump(new_price)
            if response[0] is not None:
                player_responses.append(response[0])
                if response[1]:
                    fast_players.append(i+1)
                else:
                    slow_players.append(i+1)

        random.shuffle(fast_players)
        random.shuffle(slow_players)

        time.sleep(0.1)

        if fast_players:
            for i in fast_players:
                log.debug('Group%d: fast player%d moves.' % (self.id, players[i-1].id_in_group))
                self.send_exchange(player_responses[i-1])

        time.sleep(0.4)

        if slow_players:
            for i in slow_players:
                log.debug('Group%d: slow player%d moves.' % (self.id, players[i-1].id_in_group))
                self.send_exchange(player_responses[i-1])

    def export_orders(self):
        pids = [self.player_set.all().values('id')]
        orders = serializers.serialize("json", Order.objects.filter(player_id__in=pids))
        df = pd.read_json(data)
        filename = os.path.join(os.getcwd(), '/logs/group' + self.id + '.csv')
        df.to_csv(filename)



class Player(BasePlayer):

    # basic state variables
    state = models.StringField(initial='OUT')
    speed = models.BooleanField(initial=0)  # 0 or 1
    spread = models.IntegerField(initial=2000)
    channel = models.StringField()
    # fundamental price
    fp = models.IntegerField(initial=10000)
    order_count = models.IntegerField(initial=1)

    # Player actions

    def stage_enter(self, side, price=None, time_in_force=99999):
        """
        defaults to maker enter order
        returns relevant ouch message
        """
        spread = (self.spread if side == 'S' else - self.spread)
        price = (int(self.fp + spread / 2) if not price else price)
        order = self._create_order(side=side, price=price, o_type='O', time_in_force=time_in_force)
        ouch = translate.enter(order)
        log.info('Player%d: Stage: Enter %s: %s.' % (self.id_in_group, order.side, order.token))
        return ouch

    def stage_replace(self, order):
        spread = (self.spread if order.side == 'S' else - self.spread)
        price = int(self.fp + spread / 2)
        order.stage_update('R')
        new_order = self._create_order(side=order.side, price=price, time_in_force=99999)
        ouch = translate.replace(order, new_order)   
        log.info('Player%d: Stage: Replace: %s.' % (self.id_in_group, order.token))
        return ouch

    def stage_cancel(self, order):
        order.stage_update('C')
        ouch = translate.cancel(order.token)
        log.info('Player%d: Stage: Cancel: %s.' % (self.id_in_group, order.token))
        return ouch

    def _create_order(self, **kwargs):
        order = self.order_set.create(**kwargs)
        order.stage()
        return order

    def _enter_market(self):
        log.debug('Player%d: Enters market.' % (self.id_in_group)) 
        msgs = [self.stage_enter('B'), self.stage_enter('S')]
        self.group.send_exchange(msgs, delay=True, speed=self.speed)

    def _leave_market(self):
        ords = self.order_set.filter(status='A')
        if ords:
            msgs = [self.stage_cancel(o) for o in ords]
            self.group.send_exchange(msgs, delay=True, speed=self.speed)
        else:
            log.debug('Player%d: No active orders.' % self.id_in_group)
   

    # Client actions
    def update_state(self, message):
        states = {
            'OUT':self._leave_market,
            'SNIPER':self._leave_market,
            'MAKER':self._enter_market
        }
        new_state = message['state']
        try:
            states[new_state]()
        except KeyError:    # Is this even possible ? why check ?
            log.warning('Player%d: Invalid state update.' % self.id_in_group)
        self.state = new_state
        self.save()
        log.info('Player%d: State update: %s.' % (self.id_in_group, self.state))

    def update_spread(self, message):
        self.spread = message['spread']
        self.save()
        ords = self.order_set.filter(status='A')
        if ords:
            msgs = [self.stage_replace(o) for o in ords]
            self.group.send_exchange(msgs, delay=True, speed=self.speed)
        log.info('Player%d: Spread update: %s.' % (self.id_in_group, self.spread))

    def update_speed(self, message):  
        self.speed = not self.speed      # Front end button doesnt work 0429
        self.save()
        speed = ('fast' if self.speed else 'slow')
        log.info('Player%d: Speed change: %s.' % (self.id_in_group, speed))


    # Receive methods
    def receive_from_client(self, msg):
        events= {
            'role_change':self.update_state,
            'spread_change':self.update_spread,
            'speed_change':self.update_speed
        }
        events[msg['type']](msg)

    def receive_from_group(self, msg):
        events= {
            'A':self.confirm_enter,
            'U':self.confirm_replace,
            'C':self.confirm_cancel,
            'E':self.confirm_exec
        }
        events[msg['type']](msg)

    # Confirm methods    
    # These methods should send response to clients ! 
    def confirm_enter(self,msg):
        stamp, tok = msg['timestamp'], msg['order_token']
        order = self.order_set.get(token=tok)
        order.activate(stamp)
        log.info('Player%d: Confirm: Enter: %s.' % (self.id_in_group, tok))

    def confirm_replace(self, msg):
        ptok, tok = msg['previous_order_token'], msg['order_token']
        stamp = msg['timestamp'] 
        old_order = self.order_set.get(token=ptok)
        new_order = self.order_set.get(token=tok)
        old_order.cancel(stamp)
        new_order.activate(stamp)
        log.info('Player%d: Confirm: Replace %s.' % (self.id_in_group, ptok))

    def confirm_cancel(self, msg):
        stamp, tok = msg['timestamp'], msg['order_token']
        order = self.order_set.get(token=tok)
        order.cancel(stamp)
        log.info('Player%d: Confirm: Cancel %s.' % (self.id_in_group, tok))

    def confirm_exec(self,msg):
        stamp, tok = msg['timestamp'], msg['order_token']
        order = self.order_set.get(token=tok)
        order.execute(stamp)
        log.info('Player%d: Confirm: Transaction: %s.' % (self.id_in_group, tok))
        if self.state == 'MAKER':
             log.debug('Player%d: Execution action: Enter a new order.' % self.id_in_group)
             m = [self.stage_enter(order.side)]
             self.group.send_exchange(m, delay=True, speed=self.speed)


    def jump(self, new_price):  
        old_fp = self.fp              
        self.fp = new_price
        self.save()
        postive_jump = (self.fp - old_fp) > 0

        if self.state == 'OUT':
            return [None, self.speed]

        elif self.state == 'SNIPER':
            log.debug('Player%d: Jump: Snipe.' % self.id_in_group)
            side = ('B' if postive_jump else 'S')
            order = [self.stage_enter(side, price=self.fp, time_in_force=0)]  # Special value for a market order
            return [order, self.speed]

        else:
            flag = (1 if postive_jump else 0)
            orders = self._adjust_price(flag)
            return [orders, self.speed]

    def _adjust_price(self, flag):
        sort = ('-price' if flag else 'price')
        ords = self.order_set.filter(status='A').order_by(sort)
        if ords:
            log.debug('Player%d: Jump: Replace orders in the market.' % self.id_in_group)
            msgs = [self.stage_replace(o) for o in ords]
            return msgs

    # Send to client

    def send_client(self,msg):
        Channel(str(self.channel)).send(msg)



class Investor(Model):

    group = ForeignKey(Group)
    order_count = models.IntegerField(initial=1)

    def receive_from_consumer(self, side):
        s = ('Buy' if side=='B' else 'Sell')
        log.info('Investor: %s.' % s)
        self.invest(side)

    def invest(self, side):
        p = (214748.3647 if side == 'B' else 0)
        order = Order.objects.create(side=side, price=p, time_in_force=0)
        order.token, order.firm = tokengen(0, order.side, self.order_count)
        ouch = translate.enter(order)
        logging.debug('Investor sends an order: %s' % order.token)
        self.group.send_exchange([ouch])
        self.order_count += 1
        self.save()



class Order(Model):  # This is a big object. Do we really need all these fields ?
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
    time_stage = models.IntegerField(initial=0)
    timestamp = models.IntegerField(initial=0)
    status = models.StringField(initial='S')
    update_staged = models.StringField(initial=None)
    time_canceled = models.IntegerField(initial=0)
    player = ForeignKey(Player, null=True, blank=True)


    def stage(self):
        time = Get_Time(granularity="nanoseconds")
        self.time_stage = time
        self.token, self.firm = tokengen(self.player.id_in_group, self.side, self.player.order_count)
        self.player.order_count += 1
        self.save()
        self.player.save()

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

    def stage_update(self, typ):
        time = Get_Time()
        update = str(time) + ' ' + typ
        self.update_staged = update
        self.save()



