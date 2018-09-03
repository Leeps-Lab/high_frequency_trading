#!/usr/bin/env python
import sys
import subprocess
import os
import logging
from datetime import datetime
import random
import time
import itertools
from jsonfield import JSONField
from . import translator as translate
from .hft_logging.experiment_logger import prepare
from .hft_logging import session_events as hfl
from .utility import nanoseconds_since_midnight as labtime
from . import exchange
from .profit import Price_Log, Price_Node
from channels import Group as CGroup, Channel
from otree.db.models import Model, ForeignKey
from otree.api import (
    models, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
)
from . import client_messages 
import json
from django.core.cache import cache
from .order import Order, OrderStore
import time
from . import new_translator
from .decorators import atomic
from otree.common_internal import random_chars_8
from settings import exp_logs_dir

log = logging.getLogger(__name__)

class Constants(BaseConstants):
    name_in_url = 'hft_bcs'
    players_per_group = None
    num_rounds = 2

    short_delay = 0.1   # slow players delay
    long_delay = 0.5    # fast players delay

    first_exchange_port = 9001  # make this configurable

    speed_factor = 1e-9
    player_state = ('state', 'fp', 'speed', 'spread', 'prev_speed_update')
    player_accum = ('endowment', 'cost', 'speed_on')
    player_fields = player_state + player_accum

    group_role_counts = {'OUT': 'players_per_group', 'MAKER': 0, 'SNIPER': 0}

    # cache keys
    lock_key = '{self.code}_lock'
    investor_label = 'investors_group_{self.id_in_subsession}_round_{self.round_number}'
    jump_label = 'jumps_group_{self.id_in_subsession}_round_{self.round_number}'
    player_fp_key = '{self.code}_fp'
    group_fp_key = 'group_{group_id}_fp'
    player_orderstore_key = '{self.code}_orders'
    player_status_key = '{self.code}_status'
    groups_ready_key = '{self.code}_ready'
    players_in_market_key  = '{self.code}_in_market'
    role_count_key = '{self.code}_role_count'

    unlock_value = 'unlocked'

    player_role_update_map = {
        'OUT': 'leave_market', 
        'SNIPER': 'leave_market', 
        'MAKER': 'enter_market'
    }
    player_action_map= {
        'role_change': 'update_state',
        'spread_change': 'update_spread',
        'speed_change': 'update_speed',
        'advance_me': 'session_finished',
        'player_ready': 'in_market'
    }
    player_message_handle_map = {
        'A': 'handle_enter',
        'U': 'handle_replace',
        'C': 'handle_cancel',
        'E': 'handle_exec',
    }

    # log file
    log_file = '{dir}{self.design}_{self.code}_{self.players_per_group}_{time}'

    investor_url = 'ws://127.0.0.1:8000/hft_investor/'
    jump_url = 'ws://127.0.0.1:8000/hft_jump/'

    investor_py = os.path.join(os.getcwd(), 'hft_bcs/exos/investor.py')
    jump_py = os.path.join(os.getcwd(), 'hft_bcs/exos/jump.py')
    
    conversion_factor = 1e4
    session_field_map = {
        'players_per_group': 'players_per_group',
        'round_length': 'session_length',
        'design': 'design',
        'batch_length': 'batch_length'
    }
    player_field_map = {
        'fp': 'fundamental_price',
        'spread': 'initial_spread',
        'endowment': 'initial_endowment',
        'speed_unit_cost': 'speed_cost',
        'max_spread': 'max_spread'
    }

def lablog(filename, log):
    with open(filename,'a') as f:
        f.write(log)
        f.write('\n')

subprocesses = {}
# TODO: refine this. add logging.

def stop_exogenous(group_id):
    if subprocesses[group_id]:
        for v in subprocesses[group_id].values():
            try:
                v.kill()
            except Exception as e:
                log.warning(e)
    else:
        log.warning('No subprocess found.')


class Subsession(BaseSubsession):
    design = models.StringField()
    next_available_exchange = models.IntegerField(initial=Constants.first_exchange_port)
    players_per_group = models.IntegerField()
    round_length = models.IntegerField()
    batch_length = models.IntegerField(initial=0)
    trade_ended = models.BooleanField(initial=False)
    code = models.CharField(default=random_chars_8)
    log_file = models.StringField()

    def init_cache(self):
        pairs = {}
        session_lock = Constants.lock_key.format(self=self)
        pairs[session_lock] = Constants.unlock_value
        ready_groups = Constants.groups_ready_key.format(self=self)
        pairs[ready_groups] = {g.id: False for g in self.get_groups()}
        for k, v in pairs.items():
            cache.set(k, v, timeout=None)
        print(pairs)

    def set_payoff_round(self):
        for player in self.get_players():
            payoff_round = random.randint(1, Constants.num_rounds)
            player.participant.vars['payoff_round'] = payoff_round
            player.save()

    def set_log_file(self):
        now = datetime.now().strftime('%Y-%m-%d_%H-%M')
        log_file = Constants.log_file.format(dir=exp_logs_dir, self=self, time=now)
        self.log_file = log_file
        for g in self.get_groups():
            g.log_file = log_file
            for p in g.get_players():
                p.log_file = log_file
                p.save()
            g.save()
        self.save()

    def assign_groups(self):
        group_matrix = self.session.config['group_matrix']
        self.set_group_matrix(group_matrix)
        self.save()

    def creating_session(self):
        # set session fields
        for k, v in Constants.session_field_map.items():
            setattr(self, k, self.session.config[v])
        # set default values for cached session states
        self.init_cache()
        # set group matrix
        self.assign_groups()
        # set everyone to write to same log file
        self.set_log_file()        
        if self.round_number == 1:
            # payoff from a random round will be paid.
            self.set_payoff_round()
        groups = self.get_groups()
        for group in groups:
            group.creating_group()
        players = self.get_players()
        for player in players:
            for k, v in Constants.player_field_map.items():
                v = self.session.config[v] * Constants.conversion_factor
                setattr(player, k, v)
            player.init_cache()

        #TODO: wtf? make this smaller
        group_players = {g.id: [p.id for p in g.get_players()] for g in groups}
        l = prepare(group=0, level='header', typ='header', groups=group_players,
            session=self.code, design=self.design, initial_spread=players[0].spread,
            batch_length=self.batch_length, round_length=self.round_length)
        lablog(self.log_file, l)
        self.save()
        self.session.save()

    @atomic
    def groups_ready(self, group_id, action='start'):
        k = Constants.groups_ready_key.format(self=self)
        session_state = cache.get(k)
        session_state[group_id] = True if action == 'start' else False
        cache.set(k, session_state, timeout=None)
        total = sum(session_state.values())
        if total == self.session.num_participants / self.players_per_group:
            log.info('session: starting trade, %d.' % self.round_length)
            hfl.events.dump(header=True)
            for g in self.get_groups():
                g.start()
        if total == 0 and self.trade_ended == False:
            log.info('session: advancing all players to results page.')
            self.trade_ended = True
            self.save()
            hfl.events.dump(header=True)
            self.session.advance_last_place_participants()

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

translator = new_translator.Translator()

class Group(BaseGroup):

    exch_host = models.StringField()
    exch_port = models.IntegerField()
    investor_file = models.StringField()
    jump_file = models.StringField()
    is_trading = models.BooleanField(initial=False)
    code = models.CharField(default=random_chars_8)
    log_file = models.StringField()

    def init_cache(self):
        pairs = {}
        group_lock = Constants.lock_key.format(self=self)
        pairs[group_lock] = Constants.unlock_value
        in_market_key= Constants.players_in_market_key.format(self=self)   
        pairs[in_market_key] = {p.id: False for p in self.get_players()}
        role_count_key = Constants.role_count_key.format(self=self)
        pairs[role_count_key] = {k: getattr(self.subsession, v) if isinstance(v, str) else v
                                    for k, v in Constants.group_role_counts.items()} 
        for k, v in pairs.items():
            cache.set(k, v, timeout=None)
        print(pairs)

    def creating_group(self):
        self.exch_host = self.session.config['exchange_host']
        self.exch_port = self.subsession.next_available_exchange
        self.subsession.next_available_exchange += 1
        investors = Constants.investor_label.format(self=self)
        jumps = Constants.jump_label.format(self=self)
        self.investor_file = self.session.config[investors]
        self.jump_file = self.session.config[jumps]
        fp = self.session.config['fundamental_price'] * Constants.conversion_factor
        self.fp_push(fp)
        self.init_cache()
        subprocesses[self.id] = dict()
        self.save()
        self.subsession.save()

    def start(self):
        self.spawn(
            Constants.investor_py,
            Constants.investor_url,
            self.investor_file
        )
        self.spawn(
            Constants.jump_py,
            Constants.jump_url,
            self.jump_file
        )
        self.connect_to_exchange()
        self.start_exchange()
        self.broadcast(
            client_messages.start_session()
        )
        l = prepare(group=self.id, level='exch', typ='start')
        lablog(self.log_file, l)
        self.is_trading = True
        self.save()

    @atomic
    def end_trade(self, player_id):
        if self.is_trading == True:
            log.info('Group%d: Player%d flags session end.' % (self.id, player_id))
            stop_exogenous(self.id)
            self.disconnect_from_exchange()
            self.loggy()
            self.is_trading = False
            self.save()
            l = prepare(group=self.id, level='exch', typ='end')
            lablog(self.log_file, l)
            self.subsession.groups_ready(self.id, action='end')
        else:
            pass

    def start_exchange(self):
        """
        sends a system start message
        to the exchange to allow trade
        """
        start_ouch = translate.system_start('S')
        self.send_exchange(start_ouch)
        log_dict = {'gid': self.id, 'context': 'sent system start message'}
        hfl.events.push(hfl.exchange, **log_dict)

    def connect_to_exchange(self):
        try:
            exchange.connect(self, self.exch_host, self.exch_port, wait_for_connection=True)
        except ValueError as e:
            log.warning(e)

    def disconnect_from_exchange(self):
        exchange.disconnect(self, self.exch_host, self.exch_port)

    def send_exchange(self, msgs, delay=False, speed=False):
        """
        msgs is a list of lists
        """
        msgs_flat = [m for msg in msgs for m in msg]
        true_msgs = filter(lambda x: x is not False, msgs_flat)
        if delay:
            dur = Constants.short_delay if speed else Constants.long_delay
        else:
            dur = 0.
        conn = exchange.connect(self, self.exch_host, self.exch_port).connection
        for m in true_msgs:
            conn.sendMessage(m, dur)
    
    def receive_from_exchange(self, msg):
        """
        handles messages coming from the exchange
        finds the relevant player for
        passes on message the player
        also logs investor executions
        """
        msg_type, fields = translator.decode(msg)
        if msg_type == 'S':
            event = fields['event_code']
            log.info('Received system {event}'.format(event=event))
            if event in ['B', 'P']:
                self.broadcast(client_messages.batch(event=event))
            return
        token = fields.get('order_token')
        if token is None:
            token = fields.get('replacement_order_token')
        subject = token[3]
        # index 3 is subject ID
        if subject == '@':
            if msg_type == 'E':
                # log investor execution
                hfl.events.push(hfl.inv_trans, **{'gid': self.id})
            else:
                # we really do not care about
                # investor confirm at this point.
                pass
        else:
            pid = ord(subject) - 64
            # TODO: we should find a way to not make
            # this db call, it takes ages.
            player = self.get_player_by_id(pid)
            player.receive_from_group(msg_type, fields)

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
        p = subprocess.Popen(cmd)
        subprocesses[self.id][name] = p

    def fp_push(self, price):
        """
        this updates the fp for the group
        players get this
        when responding jumps
        """
        k = Constants.group_fp_key.format(group_id=self.id)
        group_fp = cache.get(k)
        if not group_fp:
            # deque ?
            group_fp = Price_Log(100, price)
        group_fp.push(labtime(), price)
        cache.set(k, group_fp, timeout=None)

    def jump_event(self, new_price):
        """
        this is the fundamental price jump
        let all client know the new price
        get automated responses
        randomize and send to exchange
        """
        self.fp_push(new_price)
        # broadcast new price to clients
        self.broadcast(client_messages.fp_change(new_price))
        # wish there was a way to not to do this db query.
        players = self.get_players()
        # each player will respond to the
        # new fundamental price information.
        log.info('Group%d: jump to %d !!' % (self.id, new_price))
        log_dict = {'gid': self.id, 'np': new_price}
        hfl.events.push(hfl.jump, **log_dict)
        
        responses = self._collect_responses(players, new_price)
        # then we shuffle responses and send to the exchange
        self._shuffle_and_send(responses)
        # this is here since we are still debugging,
        # most of the action happen within this function
        # and some checks raise flags here.
        self.loggy()

    def _collect_responses(self, players, price):
        responses = [(p.id, p.jump(price), p.status(field='speed')) for p in players]
        return responses


    def _shuffle_and_send(self, responses):
        # index 1 is the the response an orders list of list
        true_responses = list(filter(lambda x: x[1] is not False, responses))
        random.shuffle(true_responses)
        # index 2 is speed bool
        for r in true_responses:
            orders, speed = r[1], r[2]
            if orders:
                self.send_exchange(orders, delay=True, speed=speed)
        # we really want to log response ordering
        for speed in True, False:
            # this looks odd right now but what if
            # there were N gears.
            # index 0 is the player id
            move_order = [r[0] for r in true_responses if r[2] is speed]
            log_dict = {'gid': self.id, 'speed':speed, 'move_order': move_order}
            hfl.events.push(hfl.move_order, **log_dict)

    @atomic
    def players_in_market(self, player_id):
        k = Constants.players_in_market_key.format(self=self)
        players_in_market = cache.get(k)
        players_in_market[player_id] = True
        cache.set(k, players_in_market, timeout=None)
        total = sum(players_in_market.values())
        if self.subsession.players_per_group == total:
            log.info('Group%d: all players are in market.' % self.id)
            self.subsession.groups_ready(self.id)
        else:
            log.info('Group%d: %d players are in market.' % (self.id, total))

    # @atomic
    # def players_in_market(self, player_id=None, init=False):
    #     k = Constants.players_in_market_key.format(self=self)
    #     if init is True:
    #         players = {p.id: False for p in self.get_players()}
    #         cache.set(k, players, timeout=None)
    #         return
    #     elif player_id is not None:
    #         players = cache.get(k)
    #         players[player_id] = True
    #         cache.set(k, players, timeout=None)
    #         total = sum(players.values())
    #     else:
    #         raise ValueError('player id is none.')
    #     if self.subsession.players_per_group == total:
    #         log.info('Group%d: all players are in market.' % self.id)
    #         self.subsession.groups_ready(self.id)
    #     else:
    #         log.info('Group%d: %d players are in market.' % (self.id, total))
    
    @atomic
    def group_stats(self, old_state, new_state):
        k = Constants.role_count_key.format(self=self)
        group_state = cache.get(k)
        ppg = self.subsession.players_per_group
        group_state[old_state] -= 1
        group_state[new_state] += 1
        cache.set(k, group_state, timeout=None)
        total = sum(group_state.values())
        self.broadcast(
            client_messages.total_role(group_state)
        )
        if total != ppg:
            raise ValueError('total: %d, ppg: %d' % (total, ppg))

    # @atomic
    # def group_stats(self, old_state, new_state, init=False):
    #     k = Constants.state_count_key.format(self=self)
    #     if init:
    #         ppg = self.subsession.players_per_group
    #         group_state = {
    #             'MAKER': 0, 'SNIPER':0, 'OUT': ppg
    #         }
    #         cache.set(k, group_state, timeout=None)
    #         return
    #     group_state = cache.get(k)
    #     group_state[old_state] -= 1
    #     group_state[new_state] += 1
    #     cache.set(k, group_state, timeout=None)
    #     total = sum(group_state.values())
    #     self.broadcast(
    #         client_messages.total_role(group_state)
    #     )
    #     if total != ppg:
    #         raise ValueError('total: %d, ppg: %d' % (total, self.subsession.players_per_group))


    def loggy(self):
        hfl.events.convert()
        hfl.events.dump()


class Player(BasePlayer):

    # basic state variables
    state = models.StringField(initial='OUT')
    speed = models.BooleanField(initial=False)
    spread = models.IntegerField()
    channel = models.CharField(max_length=255)
    cost = models.IntegerField(initial=0)
    fp = models.IntegerField()
    endowment = models.IntegerField()
    prev_speed_update = models.BigIntegerField(initial=0)
    speed_on = models.IntegerField(initial=0)
    speed_unit_cost = models.IntegerField()
    max_spread = models.IntegerField()
    code = models.CharField(default=random_chars_8)
    log_file = models.StringField()

    def init_cache(self):
        pairs = {}
        lock_key = Constants.lock_key.format(self=self)
        pairs[lock_key] = Constants.unlock_value
        orderstore_key = Constants.player_orderstore_key.format(self=self)
        pairs[orderstore_key] = OrderStore(self.id, self.id_in_group)
        state_key = Constants.player_status_key.format(self=self)
        pairs[state_key] = {k: getattr(self, k, None) for k in Constants.player_fields}
        for k, v in pairs.items():
            cache.set(k, v, timeout=None)  
        print(pairs)     
    
    def stage_enter(self, center='fp', side=None, price=None, time_in_force=99999):
        """
        create an enter order
        default to maker enter order
        return ouch message list
        """
        current_spread = self.status(field='spread')
        if center == 'fp':
            fp = self.status(field='fp')
        spread = current_spread if side == 'S' else - current_spread
        price = int(fp + spread / 2) if not price else price
        orderstore = self.order_store()
        order = orderstore.create(
            status='stage', side=side, price=price, time_in_force=time_in_force
        )
        self.save_order_store(orderstore)
        log_dict = {
            'gid': self.group_id, 'pid': self.id, 'state': self.status(field='state'),
            'speed': self.status(field='speed'), 'order': order
        }
        hfl.events.push(hfl.stage_enter, **log_dict)
        ouch = [translate.enter(order)]
        return ouch

    def stage_replace(self, order):
        """
        replace existing order
        create a new order
        return ouch message list
        """
        new_order, replace = self._replace(order)
        msgs = [translate.replace(o, new_order) for o in replace.values() 
                                                            if o is not False]
        log_dict = {
            'gid': self.group_id, 'pid': self.id, 'state': self.status(field='state'),
            'speed': self.status(field='speed'), 'head': replace['head'], 'new': new_order,
        }
        if len(msgs) > 1:
            log_dict['root'] = order
        hfl.events.push(hfl.stage_replace, **log_dict)
        return msgs

    def _replace(self, order):
        """
        this is the function that does orderstore
        operations, find the head order
        also replace the root if root is not head
        """
        spread = self.status(field='spread')
        d = spread / 2 if order.side == 'S' else - spread / 2
        price = int(self.status(field='fp') + d)
        orderstore = self.order_store()
        new_order = orderstore.create(
            status='replace', side=order.side, price=price, time_in_force=99999
        )
        replace = {'root': order, 'head': False}
        # find the most recent update
        order_to_replace = orderstore.find_head(order)
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
        orderstore[order_to_replace.token] = order_to_replace
        orderstore[order.token] = order
        # update and save orderstore

        self.save_order_store(orderstore)
        return (new_order, replace)

    def stage_cancel(self, order):
        """
        create a cancel order message
        return ouch message list
        """
        cancel = self._cancel(order)
        # TODO: translate cancel takes order.token,
        # translate replace takes order
        # make this uniform somehow
        msgs = [translate.cancel(o.token) for o in cancel.values()
                                                if o is not False]
        log_dict = {
            'gid': self.group_id, 'pid': self.id, 'state': self.status(field='state'),
            'speed': self.status(field='speed'), 'head': cancel['head'],
        }
        if len(msgs) > 1:
            log_dict['root'] = order
        hfl.events.push(hfl.stage_cancel, **log_dict)
        return msgs

    def _cancel(self, order):
        """
        does orderstore operations
        similar function to _replace
        """
        cancel = {'root': order, 'head': False}
        orderstore = self.order_store()
        order_to_cancel = orderstore.find_head(order)
        cancel['head'] = order_to_cancel
        if order_to_cancel is False:
            # better log this each time each happens
            # made possible by design tho
            cancel['root'] = False
        return cancel

    def enter_market(self):
        """
        enter market after switching role to maker
        send two enter ouch messages to exchange via group
        """
        msgs = [self.stage_enter(side='B'), self.stage_enter(side='S')]
        self.group.send_exchange(msgs, delay=True, speed=self.speed)

    def orders_in_market(self):
        orderstore = self.order_store()
        orders = orderstore.all_enters() 
        counts = orderstore.counts()
        count_log = {
            'gid': self.group_id, 'pid': self.id, 'act_count': counts['active'],
            'stg_count': counts['stage'],
        }
        orders_log = {
            'gid': self.group_id, 'pid': self.id, 'orders': orders
        }
        hfl.events.push(hfl.order_count, **count_log)
        hfl.events.push(hfl.orders, **orders_log)
        if len(orders) > 2:     # this has to hold if all works properly.
            log.warning('more than two enter orders: %s.' % orders)
        return orders

    def leave_market(self):
        """
        exit market after switching from maker
        pass two ouch messages to cancel active orders
        """
        orders = self.orders_in_market()
        if orders:
            msgs = [self.stage_cancel(o) for o in orders]
            self.group.send_exchange(msgs, delay=True, speed=self.speed)
        else:
            log_dict = {'gid': self.group_id, 'pid': self.id}
            hfl.events.push(hfl.no_orders, **log_dict)
        self.group.broadcast(
            client_messages.spread_change(self.id_in_group)
        )

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

    # Client actions

    @atomic
    def update_state(self, message):
        """
        switch between 3 roles (states): out, sniper and maker
        """
        states = Constants.player_role_update_map
        old_state = self.status(field='state')
        new_state = message['state'].upper()
        # update dict that keeps totals for roles
        # update player status
        self.status_update(new_state, field='state')
        try:
            # new state determines the action.
            methodname = states[new_state]
            getattr(self, methodname)()
        except KeyError:
            log.info(new_state)
            log.info('Player%d: Invalid state update.' % self.id)
        self.group.group_stats(old_state, new_state)
        log_dict = {
                'gid': self.group_id, 'pid': self.id, 'state': new_state
            }
        hfl.events.push(hfl.state_update, **log_dict)
        l = prepare(
            group=self.group_id, level='choice', typ='state',
            pid=self.id, nstate=new_state
        )
        lablog(self.log_file, l)

    @atomic
    def update_spread(self, message):
        """
        makers can change their spreads
        read new spread
        let all clients know
        replace existing orders with new price
        """
        new_spread = int(message['spread'])
        self.status_update(new_spread, field='spread')
        log_dict = {'gid': self.group_id, 'pid': self.id, 'spread': new_spread}
        hfl.events.push(hfl.spread_update, **log_dict)
        msgs = self.makers_replace(1)  # replace orders, start from above
        self.group.send_exchange(msgs, delay=True, speed=self.speed)
        l = prepare(
            group=self.group_id, level='choice', typ='spread',
            pid=self.id, nspread=new_spread
        )
        lablog(self.log_file, l)

    def update_speed(self, message):
        """
        switch between slow and fast
        calculate cost if player turns off speed
        record time if player turns on speed
        """
        new_speed = not self.status(field='speed')
        self.status_update(new_speed, field='speed')
        now = labtime()
        if new_speed:
            self.status_update(now, field='prev_speed_update')
        else:
            start = self.status(field='prev_speed_update')
            total_time = now - start
            self.status_update(total_time, field='speed_on')
        log_dict = {'gid': self.group_id, 'pid': self.id, 'speed': new_speed}
        hfl.events.push(hfl.speed_update, **log_dict)
        l = prepare(
            group=self.group_id, level='choice', typ='speed',
            pid=self.id, nspeed=new_speed
        )
        lablog(self.log_file, l)

    def in_market(self, msg):
        log.info('Group%d: Player%d: In market.' % (self.group_id, self.id))
        self.group.players_in_market(self.id)

    def session_finished(self, msg):
        log.info('Group%d: Player%d: Ready to advance.' % (self.group_id, self.id))
        if self.subsession.trade_ended == False:
            self.group.end_trade(self.id)

    # Receive methods
    # action starts here

    def receive_from_client(self, msg):
        """
        consumers call this when
        oTree receives a websocket frame
        from a client
        """
        actions = Constants.player_action_map
        methodname = actions[msg['type']]
        getattr(self, methodname)(msg)

    def receive_from_group(self, header, body):
        handlers = Constants.player_message_handle_map
        methodname = handlers[header]
        getattr(self, methodname)(body)
        # this next line is just for debugging
        # I like it because it prints orderstore.
        # comes cheap since all the processing
        # is done, just blocks a worker.
        self.orders_in_market()

    """
    update order_store when
    player receives a message
    from the exchange
    """

    def makers_broadcast(self, token):
        # message front-ends so they can place ticks
        # what is my fundamental price and spread ?
        fp  = self.status(field='fp')
        spread = self.status(field='spread')
        # then these are legs
        lo, hi = fp - spread / 2, fp + spread / 2
        self.group.broadcast(
            client_messages.spread_change(self.id_in_group, leg_up=hi, leg_low=lo, token=token)
        )

    # Confirm methods

    @atomic
    def handle_enter(self, msg):
        """
        handle accept messages for the player
        update order status as active
        """
        stamp, tok = msg['timestamp'], msg['order_token']
        order = self._confirm_enter(stamp, tok)
        current_state = self.status(field='state')
        # TODO: make base roles point instead of hardcoding
        if current_state == 'MAKER':
            self.makers_broadcast(tok)
        l = prepare(
            group=self.group_id, level='exch', typ='enter',
            pid=self.id, token=order.token, stamp=order.timestamp,
            side=order.side, tif=order.time_in_force, price=order.price
        )
        lablog(self.log_file, l)

    def _confirm_enter(self, stamp, token):
        """
        orderstore operations when confirm
        """
        orderstore = self.order_store()
        order = orderstore[token]
        if not order:
            log.warning('player %s: order %s not in active orders' % (self.id, token))
        # update order as active
        order = orderstore.activate(stamp, order)
        self.save_order_store(orderstore)
        log_dict = {'gid': self.group_id, 'pid': self.id, 'order': order}
        hfl.events.push(hfl.confirm_enter, **log_dict)
        return order

    @atomic
    def handle_replace(self, msg):
        """
        handle replaced messages for the player
        """
        ptoken, token = msg['previous_order_token'], msg['replacement_order_token']
        stamp = msg['timestamp']
        old_order, new_order = self._confirm_replace(stamp, ptoken, token)
        current_state = self.status(field='state')
        if current_state == 'MAKER':
            self.makers_broadcast(token)
        l = prepare(
            group=self.group_id, level='exch', typ='replace',
            pid=self.id, old_token=old_order.token,
            new_token=new_order.token, stamp=new_order.timestamp,
        )
        lablog(self.log_file, l)


    def _confirm_replace(self, stamp, ptoken, token):
        orderstore = self.order_store()
        old_order = orderstore[ptoken]
        new_order = orderstore[token]
        if not old_order:
            log.warning('player %s: order %s is not in active orders' % (self.id, ptoken))
        if not new_order:
            log.warning('player %s: order %s is not in active orders.' % (self.id, token))
        old_order = orderstore.inactivate(old_order, 'replaced')
        new_order = orderstore.activate(stamp, new_order)
        self.save_order_store(orderstore)
        log_dict = {
            'gid': self.group_id, 'pid': self.id,
            'replaced': old_order, 'replacing': new_order,
        }
        hfl.events.push(hfl.confirm_replace, **log_dict)
        return (old_order, new_order)

    @atomic
    def handle_cancel(self, msg):
        """
        handles canceled messages
        find canceled order in the order store
        move it to inactive dict
        update order state as canceled
        """
        stamp, tok = msg['timestamp'], msg['order_token']
        order = self._confirm_cancel(stamp, tok)
        l = prepare(
            group=self.group_id, level='exch', typ='cancel',
            pid=self.id, token=order.token, stamp=order.timestamp
        )
        lablog(self.log_file, l)

    def _confirm_cancel(self, stamp, token):
        orderstore = self.order_store()
        order = orderstore[token]
        if not order:
            log.warning('player %s : canceled order %s not found in active orders.' % (self.id, token) )
        order = orderstore.inactivate(order, 'canceled')
        self.save_order_store(orderstore)
        log_dict = {'gid': self.group_id, 'pid': self.id, 'order': order}
        hfl.events.push(hfl.confirm_cancel, **log_dict)
        return order

    @atomic
    def handle_exec(self, msg):
        """
        handles execution messages
        update order state as executed
        take profit
        """
        stamp, tok = msg['timestamp'], msg['order_token']
        order = self._confirm_exec(stamp, tok)
        price = msg['execution_price']
        profit = self.profit(price, order.side, stamp)
        self.group.broadcast(
            client_messages.execution(self.id_in_group, tok, profit)
        )
        self.post_execution(order)
        l = prepare(
            group=self.group_id, level='exch', typ='exec',
            pid=self.id, token=order.token, price=order.price, 
            stamp=order.timestamp
        )
        lablog(self.log_file, l)

    def _confirm_exec(self, stamp, token):
        orderstore = self.order_store()
        order = orderstore[token]
        order = orderstore.inactivate(order, 'executed')
        self.save_order_store(orderstore)
        log_dict = {'gid': self.group_id, 'pid': self.id, 'order': order}
        hfl.events.push(hfl.confirm_exec, **log_dict)
        return order
    
    def post_execution(self, order, kind='bcs_post_execution'):
        post_exec_func = getattr(self, kind)
        assert post_exec_func
        post_exec_func(order)
    
    def bcs_post_execution(self, order):
        current_state = self.status(field='state')
        if current_state == 'MAKER' and order.time_in_force != 0:
            msgs = [self.stage_enter(side=order.side)]
            self.group.send_exchange(msgs, delay=True, speed=self.speed)

    def profit(self, exec_price, side, timestamp, kind='bcs_profit'):
        profit_func = getattr(self, kind)
        assert profit_func
        pi = profit_func(exec_price, side, timestamp)
        return pi

    def bcs_profit(self, exec_price, side, timestamp):
        fp_key = Constants.group_fp_key.format(group_id=self.group_id)
        fp = cache.get(fp_key).get_FP(timestamp)
        d = abs(fp - exec_price)
        if exec_price < fp:
            # buyer (seller) buys (sells) less than fp
            pi = d if side == 'B' else -d  
        else:
            # seller (buyer) sells (buys) higher than fp
            pi = d if side == 'S' else -d  
        self.status_update(pi, field='endowment')
        log_dict = {
            'gid': self.group_id, 'pid': self.id, 'amount': pi,
            'side': side, 'profit': self.status(field='endowment'), 'fp': fp, 
            'p': exec_price,
        }
        hfl.events.push(hfl.profit, **log_dict)
        l = prepare(
            group=self.group_id, level='market', typ='profit',
            source='cross', pid=self.id, stamp=timestamp,
            endowment=self.status(field='endowment'), profit=pi
        )
        lablog(self.log_file, l)
        return pi    
   
    # def calc_profit(self, exec_price, side, timestamp):
    #     """
    #     find the distance btw fundamental and execution prices
    #     order side determines profit sign
    #     take speed cost along the way
    #     """
    #     fp_key = Constants.group_fp_key.format(group_id=self.group_id)
    #     fp = cache.get(fp_key).get_FP(timestamp)
    #     d = abs(fp - exec_price)
    #     profit = self.status('profit')
    #     if exec_price < fp:
    #         # buyer (seller) buys (sells) less than fp
    #         pi = d if side == 'B' else -d  
    #     else:
    #         # seller (buyer) sells (buys) higher than fp
    #         pi = d if side == 'S' else -d  
    #     updated_profit = profit + pi
    #     self.status_update('profit', updated_profit)
    #     log_dict = {
    #         'gid': self.group_id, 'pid': self.id, 'amount': pi,
    #         'side': side, 'profit': updated_profit, 'fp': fp, 
    #         'p': exec_price,
    #     }
    #     hfl.events.push(hfl.profit, **log_dict)
    #     if self.status('speed'):
    #         self._calc_speed_cost(labtime())
    #     l = prepare(
    #         group=self.group_id, level='market', typ='profit',
    #         source='cross', pid=self.id, stamp=timestamp,
    #         endowment=updated_profit, profit=pi
    #     )
    #     lablog(self.log_file, l)
    #     return pi

    def take_cost(self, kind='bcs_speed_cost'):
        now = labtime()
        cost_func = getattr(self, kind)
        cost_func(now)
    
    def bcs_speed_cost(self, timestamp):
        """
        this should only be called once at session end
        can edit for different versions
        """
        if self.status(field='speed') is True:
            self.update_speed('')   # sorry 
        delta = self.status(field='speed_on')
        amount = self.speed_unit_cost * delta * Constants.speed_factor
        self.status_update(amount, field='cost')
        log_dict = {
            'gid': self.group_id, 'pid': self.id,
            'amount': amount, 'delta': delta, 'cost': amount
        }
        hfl.events.push(hfl.cost, **log_dict)
        l = prepare(
            group=self.group_id, level='market', typ='cost',
            source='speed', pid=self.id, stamp=timestamp,
            cost=amount
        )
        lablog(self.log_file, l)

    def calc_payoff(self):
        profit = self.status(field='endowment')
        cost = self.status(field='cost')
        payoff = profit - cost
        return payoff
        


    # def _calc_speed_cost(self, timestamp):
    #     """
    #     calculate speed cost since the previous calculation
    #     """
    #     delta = timestamp - self.status('speed_change_time')
    #     # TODO: move factor to somewhere else.
    #     nanocost = self.speed_cost * 1e-9
    #     cost = delta * nanocost
    #     self.status_update('speed_change_time', timestamp)
    #     new_profit = self.status('profit') - cost
    #     self.status_update('profit', new_profit)
    #     log_dict = {
    #         'gid': self.group_id, 'pid': self.id,
    #         'cost': cost, 'delta': delta, 'nanocost': nanocost
    #     }
    #     hfl.events.push(hfl.cost, **log_dict)
    #     l = prepare(
    #         group=self.group_id, level='market', typ='profit',
    #         source='speed', pid=self.id, stamp=timestamp,
    #         endowment=new_profit, profit=-cost
    #     )
    #     lablog(self.log_file, l)

    @atomic
    def jump(self, new_price):
        """
        player's response to jump
        update fundamental price
        return jump response to group.jump
        """
        is_positive = new_price - self.status(field='fp') > 0.
        self.status_update(new_price, field='fp')
        response = False
        current_role = self.status(field='state')

        if current_role == 'SNIPER':
            side = 'B' if is_positive else 'S'
            order = [self.stage_enter(side=side, price=self.status(field='fp'), time_in_force=0)]
            response = order
        elif current_role == 'MAKER':
            flag = 1 if is_positive else 0
            orders = self.makers_replace(flag)  # makers replace returns 2 ouch messages
            response = orders
        else:
            pass
        
        return response

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


    def order_store(self, init=False):
        """
        player's order store
        lives in cache backend
        """
        k = Constants.player_orderstore_key.format(self=self)
        orderstore = cache.get(k, None)               
        return orderstore

    def save_order_store(self, orderstore):
        """
        write orderstore back to cache
        """
        k = Constants.player_orderstore_key.format(self=self)
        cache.set(k, orderstore, timeout=None)
        

    # def fp(self):
    #     """
    #     each player stores a fundamental price on cache
    #     read from cache
    #     return fp
    #     """
    #     k = Constants.player_fp_key.format(self=self)
    #     fp = cache.get(k)
    #     if not fp:
    #         fp = self.default_fp
    #         log.info(
    #             'Group%d: Player%d: Initiate FP as %d .' % (self.group_id, self.id, fp)
    #         )
    #         cache.set(k, fp, timeout=None)
    #     return fp

    # def fp_update(self, new_fp):
    #     k = Constants.player_fp_key.format(self=self)
    #     cache.set(k, new_fp, timeout=None)
        # log.info('Group%d: Player%d: Update FP: %d' % (self.group_id, self.id, new_fp))
    
    # def status(self, field=None, init=False):
    #     if field is None:
    #         raise ValueError
    #     if init:
    #         status = {k: getattr(self, k, None) for k in Constants.player_status_fields}
    #         # TODO: also add accumulated fields
    #         cache_key = Constants.player_status_key.format(self=self)
    #         cache.set(k, status, timeout=None)
    #     else:
    #         status = cache.get(k, None)
    #     assert status is not None
    #     out = status.get(field)
    #     assert out is not None
    #     return out

    def status(self, field=None):
        k = Constants.player_status_key.format(self=self)
        status = cache.get(k, None)
        out = status[field]
        return out

    def status_update(self, new, field=None):
        k = Constants.player_status_key.format(self=self)
        status = cache.get(k)
        if field in Constants.player_state:
            status[field] = new
        elif field in Constants.player_accum:
            status[field] += new
        else:
            raise ValueError('invalid field.') 
        cache.set(k, status, timeout=None)

    # def status_update(self, new_state, field=None):
    #     k = Constants.player_status_key.format(self=self)
    #     status = cache.get(k)
    #     status[field] = new_state
    #     cache.set(k, status, timeout=None)

class Investor(Model):

    group = ForeignKey(Group)
    order_count = models.IntegerField(initial=1)

    def receive_from_consumer(self, side):
        s = ('buy' if side=='B' else 'sell')
        log.info('Group%d: investor%d: %s.' % (self.group.id, self.order_count, s))
        self.invest(side)

    def invest(self, side):
        p = (2147483647 if side == 'B' else 0)
        order = Order(
            pid= 0, count=self.order_count, status='stage', 
            side=side, price=p, time_in_force=self.group.subsession.batch_length  # LOL
        )
        ouch = [translate.enter(order)]
        self.group.send_exchange([ouch])   # send exchange expects list of lists
        self.order_count += 1
        self.save()
