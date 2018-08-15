#!/usr/bin/env python
import sys
import subprocess
import os
import logging
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
from django_redis import get_redis_connection
import redis_lock
from redis.lock import Lock, LuaLock
from . import new_translator
from .decorators import atomic
from functools import partial


log = logging.getLogger(__name__)

group_atomic = partial(atomic, 'group')
player_atomic = partial(atomic, 'player')


class Constants(BaseConstants):
    name_in_url = 'hft_bcs'
    players_per_group = None
    num_rounds = 1

    short_delay = 0.1   # slow players delay
    long_delay = 0.5    # fast players delay

    investor_url = 'ws://127.0.0.1:8000/hft_investor/'
    jump_url = 'ws://127.0.0.1:8000/hft_jump/'

    investor_py = os.path.join(os.getcwd(), 'hft_bcs/exos/investor.py')
    jump_py = os.path.join(os.getcwd(), 'hft_bcs/exos/jump.py')


subprocesses = {}
# TODO: refine this. add logging.

def stop_investors(subs):
    if subs:
        for v in subs.values():
            try:
                v.kill()
            except Exception as e:
                log.info(e)
    else:
        log.warning('No subprocess found.')


class Subsession(BaseSubsession):
    players_per_group = models.IntegerField()
    # player_states = JSONField()
    round_length = models.IntegerField()
    trade_ended = models.BooleanField(initial=0)

    def creating_session(self):
        # set session length
        self.round_length = self.session.config['session_length']
        log.info('Session length: %d.' % self.round_length)
        # configurable group size, copy from oTree docs.
        group_matrix = []
        players = self.get_players()
        ppg = self.session.config['players_per_group']
        self.players_per_group = ppg
        for i in range(0, len(players), ppg):
            group_matrix.append(players[i:i+ppg])
        self.set_group_matrix(group_matrix)
        for i, g in enumerate(self.get_groups()):
            g.exch_host = self.session.config['exchange_host']
            # each group gets an exchange
            g.exch_port = 9000 + i + 1
            # read in investor and jump arrival times
            investors = 'investors_group' + '_' + str(i + 1)
            jumps = 'jumps_group' + '_' + str(i + 1)
            g.investor_file = self.session.config[investors]
            g.jump_file = self.session.config[jumps]
            # g.json = {
            #     "messages": [],
            # }
            #
            lock_key = str(self.id) + 'lock'
            #
            cache.set(lock_key, 'unlocked', timeout=None)
            first_price = self.session.config['fundamental_price'] * 1e4
            g.fp_push(first_price)
            g.save()

        # self.player_states = {
        #     "is_live": {},
        #     "ready_to_advance": {},
        # }

        # location of Price_Log object
        # only log last 10 jumps.

        for p in players:
            # initiate fields in postgres here,
            # these will not be updated dynamically
            # only used to initiate some front-end variables
            p.default_fp = first_price
            p.spread = self.session.config['initial_spread'] * 1e4
            p.profit = self.session.config['initial_endowment'] * 1e4
            p.speed_cost = self.session.config['speed_cost'] * 1e4
            p.max_spread = self.session.config['max_spread'] * 1e4
            # initiate some fields on redis also.
            o = p.order_store(init=True)
            p.status('state')
            lock_key = str(p.id) + 'lock'
            cache.set(lock_key, 'unlocked')
            p.save()
        self.save()
        self.session.save()

    # def player_can_leave(self, player_id):
    #     print(player_id)
    #     advancing = self.player_states["ready_to_advance"]
    #     advancing[player_id] = True
    #     total_advancing = sum(advancing.values())
    #     self.player_states["ready_to_advance"] = advancing
    #     self.save()
    #     log.info('Session: %d players are ready to advance to results page.' % total_advancing)
    #     if total_advancing == self.live_count():  # in case people gets dc ed
    #         log.info('All players are ready to advance.')
    #         self.session.advance_last_place_participants()

    def end_trade(self, player_id):
        log.info('Session: Player%d made to session end.' % player_id)
        stop_investors(subprocesses)
        groups = self.get_groups()
        for g in groups:
            g.disconnect_from_exchange()
            g.loggy()
        self.session.advance_last_place_participants()

    def groups_ready(self, group_id):
        k = 'session_stats_' + str(self.id)
        session_state = cache.get(k)
        if not session_state:
            session_state = dict()
        session_state[group_id] = True
        cache.set(k, session_state, timeout=None)
        total = sum(session_state.values())
        log.info('Session: %d groups ready to start.' % total)
        if total == self.session.num_participants / self.players_per_group:
            log.info('Session: Starting trade, %d.' % self.round_length)
            hfl.events.dump(header=True)
            for g in self.get_groups():
                g.start()

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
    is_trading = models.BooleanField(initial=0)
    # ready_players = models.IntegerField(initial=0)

    def start(self):
        self.connect_to_exchange()
        self.start_exchange()
        self.broadcast(
            client_messages.start_session()
        )
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
        self.is_trading = True
        self.save()
    #TODO: write an connector object and let each group have one.
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
        log.info('Group%d: Connected to exchange on port %d' % (self.id, self.exch_port))

    def disconnect_from_exchange(self):
        exchange.disconnect(self, self.exch_host, self.exch_port)
        log.info('Group%d: Disconnected from exchange on port %d' % (self.id, self.exch_port))

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
    

    # def receive_from_exchange(self, msg):
    #     """
    #     handles messages coming from the exchange
    #     finds the relevant player for
    #     passes on message the player
    #     also logs investor executions
    #     """
    #     translator.decode(msg)
    #     msg_format = (msg[0], len(msg))   # index 0 is message type
    #     try:
    #         # use message format to
    #         # determine inbound message type
    #         ouch = translate.get_types()[msg_format](msg)
    #         if ouch['type'] == 'S':
    #             # not interested in system messages yet.
    #             return
    #     except KeyError:
    #         msg_type, msg_len = chr(msg[0]), len(msg)
    #         log.warning('Group{}: received type-{}:length-{}'.format(self.id, msg_type, msg_len))
    #     # index 3 is subject ID
    #     owner = ouch['order_token'][3]
    #     if owner == '@':
    #         if ouch['type'] == 'E':
    #             # log investor execution
    #             hfl.events.push(hfl.inv_trans, **{'gid': self.id})
    #         else:
    #             # we really do not care about
    #             # investor confirm at this point.
    #             pass
    #     else:
    #         pid = ord(owner) - 64
    #         # TODO: we should find a way to not make
    #         # this db call, it takes ages.
    #         player = self.get_player_by_id(pid)
    #         player.receive_from_group(ouch)

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
        # TODO: more control asap
        log.info('Group%d: Fire %s.' % (self.id, name))
        cmd = ['python', name, str(self.id), url, data]
        p = subprocess.Popen(cmd)
        subprocesses[name] = p

    # def jump_event(self, new_price):
    #     log.info('-----------Jump Start---------------')
    #     t =time.time()
    #     lablog = prepare(
    #         group=self.id, level='env', typ='jump', fp=new_price
    #     )
    #     log.experiment(lablog)
    #     diff = time.time() - t
    #     print('Lablog jump took: ', diff*1000)
    #     log.info('Group%d: Jump, new price is %d!' % (self.id, new_price) )
    #     # Check if group.id is the designated FPC updater
    #     t = time.time()
    #     if cache.get('profit_pusher') == self.id:
    #         # Push new profit to Price_Log
    #         fp_log = cache.get('FP_Log')
    #         fp_log.push(labtime(), new_price)
    #         cache.set('FP_Log', fp_log, timeout=None)
    #     diff = time.time() - t
    #     print('Profitfp log thing took: ', diff*1000)
    #     # broadcast new price to clients
    #     self.broadcast(ClientMessage.fp_change(new_price))
    #     # t = time.time()
    #     players = self.get_players()    # get all players
    #     # diff = time.time() - t
    #     # print('DB get players took: ', diff*1000)
    #     player_responses = []
    #     fast_players = []
    #     slow_players = []

    #     for i, player in enumerate(players):
    #         response = player.jump(new_price)   # make them respond to jump
    #         player_responses.append(response['order'])
    #         if response['order']:   # participants in the market will create new orders
    #             if response['speed']:
    #                 fast_players.append(i)
    #             else:
    #                 slow_players.append(i)

    #     if fast_players:    # shuffle fast players' response and send to exchange
    #         random.shuffle(fast_players)
    #         fast_order = [i+1 for i in fast_players]
    #         log.info(
    #             'Group{}: fast players move order: {}'.format(self.id, fast_order)
    #         )
    #         for i in fast_players:
    #             state = players[i].state
    #             pid = players[i].id_in_group
    #             log.debug(
    #                 'Group%d: fast %s player%d moves.' % (self.id, state, pid )
    #             )
    #             self.send_exchange(player_responses[i], delay=True, speed=True)
    #     else:
    #         log.info('Group%d: No fast players.' % self.id )
    #     if slow_players:    # then shuffle and send slow players' response
    #         random.shuffle(slow_players)
    #         slow_order = [i+1 for i in slow_players]
    #         log.info(
    #             'Group{}: slow players move order: {}'.format(self.id, slow_order)
    #         )
    #         for i in slow_players:
    #             state = players[i].state
    #             pid = players[i].id_in_group
    #             log.debug(
    #                 'Group%d: slow %s player%d moves.' % (self.id, state, pid)
    #             )
    #             self.send_exchange(player_responses[i], delay=True, speed=False)
    #     else:
    #         log.info('Group%d: No slow players.' % self.id)
    #     log.info('-----------Jump End---------------')

    def fp_push(self, price):
        """
        this updates the fp for the group
        players get this
        when responding jumps
        """
        k = 'group_fp_' + str(self.id)
        group_fp = cache.get(k)
        if not group_fp:
            group_fp = Price_Log(100, price)
            log.info('Group %s: Inititate price log: %s.' % (self.id, group_fp))
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
        # broadcast new price to frontends
        self.broadcast(client_messages.fp_change(new_price))
        # wish there was a way to not to do this db query.
        players = self.get_players()
        # each player will respond to the
        # new fundamental price information.
        log.info('Jump to %d' % new_price)
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
        responses = [(p.id, p.jump(price), p.status('speed')) for p in players]
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

        # players = self.get_players()    # get all players
        # player_responses = []
        # fast_players = []
        # slow_players = []

        # for i, player in enumerate(players):
        #     response = player.jump(new_price)   # make them respond to jump
        #     player_responses.append(response['order'])
        #     if response['order']:   # participants in the market will create new orders
        #         if response['speed']:
        #             fast_players.append(i)
        #         else:
        #             slow_players.append(i)

        # if fast_players:    # shuffle fast players' response and send to exchange
        #     random.shuffle(fast_players)
        #     fast_order = [i+1 for i in fast_players]
        #     log.info(
        #         'Group{}: fast players move order: {}'.format(self.id, fast_order)
        #     )
        #     for i in fast_players:
        #         state = players[i].state
        #         pid = players[i].id_in_group
        #         log.debug(
        #             'Group%d: fast %s player%d moves.' % (self.id, state, pid )
        #         )
        #         self.send_exchange(player_responses[i], delay=True, speed=True)
        # else:
        #     log.info('Group%d: No fast players.' % self.id )
        # if slow_players:    # then shuffle and send slow players' response
        #     random.shuffle(slow_players)
        #     slow_order = [i+1 for i in slow_players]
        #     log.info(
        #         'Group{}: slow players move order: {}'.format(self.id, slow_order)
        #     )
        #     for i in slow_players:
        #         state = players[i].state
        #         pid = players[i].id_in_group
        #         log.debug(
        #             'Group%d: slow %s player%d moves.' % (self.id, state, pid)
        #         )
        #         self.send_exchange(player_responses[i], delay=True, speed=False)
        # else:
        #     log.info('Group%d: No slow players.' % self.id)
        # log.info('-----------Jump End---------------')

    @atomic
    def players_in_market(self, player_id):
        k = 'player_states'+ '_' + str(self.id)
        players_in_market = cache.get(k)
        if not players_in_market:
            players_in_market = dict()
        players_in_market[player_id] = True
        cache.set(k, players_in_market, timeout=None)
        total = sum(players_in_market.values())
        if self.subsession.players_per_group == total:
            log.info('Group%d: All players are in market.' % self.id)
            self.subsession.groups_ready(self.id)
        else:
            log.info('Group%d: %d players are in market.' % (self.id, total))

    def loggy(self):
        hfl.events.convert()
        hfl.events.dump()



    # def player_dropped(self, player_id):
    #     k = 'player_states'+ '_' + str(self.id)
    #     players_in_market = cache.get(k)
    #     players_in_market[player_id] = False
    #     cache.set(k, players_in_market, timeout=None)
    #     total = sum(players_in_market.values())
    #     log.info('Group%s: %d players are in market.' % (self.id, total))

    # def update_player(self, msg):
    #     self.ready_players += 1
    #     self.save()
    #     if self.ready_players == self.subsession.players_per_group:
    #         self.broadcast(
    #             ClientMessage.start_session()
    #         )
            # ali start inv and jump





class Player(BasePlayer):

    # basic state variables
    state = models.StringField(initial='OUT')
    speed = models.BooleanField(initial=0)  # 0 or 1
    spread = models.IntegerField()
    channel = models.CharField(max_length=255)
 #  ready = models.BooleanField(initial=0)
    default_fp = models.IntegerField()
    profit = models.IntegerField()
    time_of_speed_change = models.BigIntegerField()
    speed_cost = models.IntegerField()
    max_spread = models.IntegerField()

    # Player actions
    # def __str__(self):
    #     speed = 'FAST' if self.speed else 'SLOW'
    #     t = time.time()
    #     out = '<Player {}:{}>'.format(self.state, speed)
    #     diff = time.time() - t
    #     print('player string method took: ', diff*1000)
    #     return out

    # def stage_enter(self, side, price=None, time_in_force=99999):
    #     """
    #     create an enter order
    #     default to maker enter order
    #     return ouch message list
    #     """
    #     current_spread = self.status('spread')
    #     spread = current_spread if side == 'S' else - current_spread
    #     price = int(self.fp() + spread / 2) if not price else price
    #     order = self._create_order(
    #         status='STG', side=side, price=price, time_in_force=time_in_force
    #     )
    #     log_dict = {
    #         'gid': self.group_id, 'pid': self.id, 'state': self.status('state'),
    #         'speed': self.status('speed'), 'order': order
    #     }
    #     hfl.logger.push(hfl.stage_enter, **log_dict)
    #     ouch = translate.enter(order)
    #     msgs = [ouch]
    #     return msgs

    # def stage_enter(self, side, price=None, time_in_force=99999):
    #     """
    #     create an enter order
    #     default to maker enter order
    #     return ouch message list
    #     """
    #     current_spread = self.status('spread')
    #     spread = current_spread if side == 'S' else - current_spread
    #     price = int(self.fp() + spread / 2) if not price else price
    #     orderstore = self.order_store('stage_enter',safe=True)
    #     order = orderstore.create(
    #         status='STG', side=side, price=price, time_in_force=time_in_force
    #     )
    #     self.save_order_store('stage_enter', orderstore)
    #     log_dict = {
    #         'gid': self.group_id, 'pid': self.id, 'state': self.status('state'),
    #         'speed': self.status('speed'), 'order': order
    #     }
    #     hfl.events.push(hfl.stage_enter, **log_dict)
    #     ouch = translate.enter(order)
    #     msgs = [ouch]
    #     return msgs
    
    def stage_enter(self, side=None, price=None, time_in_force=99999):
        """
        create an enter order
        default to maker enter order
        return ouch message list
        """
        current_spread = self.status('spread')
        spread = current_spread if side == 'S' else - current_spread
        price = int(self.fp() + spread / 2) if not price else price
        orderstore = self.order_store()
        order = orderstore.create(
            status='stage', side=side, price=price, time_in_force=time_in_force
        )
        self.save_order_store(orderstore)
        log_dict = {
            'gid': self.group_id, 'pid': self.id, 'state': self.status('state'),
            'speed': self.status('speed'), 'order': order
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
            'gid': self.group_id, 'pid': self.id, 'state': self.status('state'),
            'speed': self.status('speed'), 'head': replace['head'], 'new': new_order,
        }
        if len(msgs) > 1:
            log_dict['root'] = order
        hfl.events.push(hfl.stage_replace, **log_dict)
        # orderstore = self.order_store()
        # order_to_replace = orderstore.find_head(order)
        # if not order_to_replace:
        #     msgs.append(False)
        #     return msgs
        # if order_to_replace != order:
        #     ouch_main = translate.replace(order, new_order)
        #     msgs.append(ouch_main)
        # order_to_replace.to_replace(labtime(), new_order.token)
        # t = time.time()
        # orderstore.active[order_to_replace.token] = order_to_replace
        # diff = time.time() - t
        # print('orderstore activate: ', diff*1000)
        # self.save_order_store(orderstore)
        # t = time.time()
        # ouch_head = translate.replace(order_to_replace, new_order)
        # diff = time.time() - t
        # print('replace translate took: ', diff*1000)
        # msgs.append(ouch_head)
        # t = time.time()
        # lg = 'Group: Player{}: {}: Stage: Replace: {} with {}: {} & {} -> {}.'.format(
        #         self.id, self, order_to_replace.token, new_order.token,
        #         order, order_to_replace, new_order
        #     )
        # diff = time.time() - t
        # print('Stage Replace log create took: ', diff*1000)
        # t = time.time()
        # log.info(lg)
        # diff = time.time() - t
        # print('stage replace log took: ', diff*1000)
        return msgs

    def _replace(self, order):
        """
        this is the function that does orderstore
        operations, find the head order
        also replace the root if root is not head
        """
        spread = self.status('spread')
        d = spread / 2 if order.side == 'S' else - spread / 2
        price = int(self.fp() + d)
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

    # def stage_cancel(self, order):
    #     """
    #     create a cancel order message
    #     return ouch message list
    #     """
        # msgs = []
        # orderstore = self.order_store()
        # order_to_cancel = orderstore.find_head(order)
        # if not order_to_cancel:
        #     # better log this each time each happens
        #     # made possible by design tho
        #     log.info('Group%d: Player%d: Order %s: Already inactive, ignore cancel.' % (
        #         self.group_id, self.id, order_to_cancel.token )
        #     )
        #     msgs.append(False)
        #     return msgs
        # if order_to_cancel != order:
        #     log.info('Group%d: Player%d: Stage: Double cancel for safety.' % (self.group_id, self.id))
        #     ouch_main = translate.cancel(order.token)
        #     msgs.append(ouch_main)
        # ouch_head = translate.cancel(order_to_cancel.token)
        # t = time.time()
        # log.info('Group {}: Player{}: {}: Stage: Cancel: {}: {}|{}.'.format(
        #     self.group_id, self.id, self, order_to_cancel.token, order, order_to_cancel)
        # )
        # diff = time.time() - t
        # print('log cancel took: ', diff*1000)
        # msgs.append(ouch_head)
        # return msgs

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
        # orderstore = self.order_store()
        # order_to_cancel = orderstore.find_head(order)
        # if not order_to_cancel:
        #     # better log this each time each happens
        #     # made possible by design tho
        #     log.info('Group%d: Player%d: Order %s: Already inactive, ignore cancel.' % (
        #         self.group_id, self.id, order_to_cancel.token )
        #     )
        #     msgs.append(False)
        # if order_to_cancel != order:
        #     ouch_main = translate.cancel(order.token)
        log_dict = {
            'gid': self.group_id, 'pid': self.id, 'state': self.status('state'),
            'speed': self.status('speed'), 'head': cancel['head'],
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

    # def _create_order(self, **kwargs):
    #     """
    #     create a new order in player's order store
    #     save order store back in cache
    #     """
    #     orderstore = self.order_store('create order ', safe=True)
    #     order = orderstore.create(**kwargs)
    #     self.save_order_store('create order ', orderstore)
    #     return order

    def _enter_market(self):
        """
        enter market after switching role to maker
        send two enter ouch messages to exchange via group
        """
        msgs = [self.stage_enter(side='B'), self.stage_enter(side='S')]
        self.group.send_exchange(msgs, delay=True, speed=self.speed)

    def orders_in_market(self):
        orderstore = self.order_store()
        orders = orderstore.all_enters() 
        count_log = {
            'gid': self.group_id, 'pid': self.id, 'act_count': 1,
            'stg_count': 1,
        }
        orders_log = {
            'gid': self.group_id, 'pid': self.id, 'orders': orders
        }
        hfl.events.push(hfl.order_count, **count_log)
        hfl.events.push(hfl.orders, **orders_log)
        if len(orders) > 2:     # this has to hold if all works properly.
            self.group.loggy()
            log.warning('more than two enter orders: %s.' % orders)
        return orders

    # def orders_in_market(self):
    #     orderstore = self.order_store()
    #     orders = orderstore.get_all('ACT')
    #     active_count = len(orders)
    #     staged_count = 0
    #     if active_count < 2:  # maker does not have 2 active orders in the market.
    #         all_staged = orderstore.get_all('STG')
    #         #  exclude sniper orders, they are never in market.
    #         staged_orders = [o for o in all_staged if o.time_in_force is not 0]
    #         orders.extend(staged_orders)
    #         staged_count = len(staged_orders)
    #     count_log = {
    #         'gid': self.group_id, 'pid': self.id, 'act_count': active_count,
    #         'stg_count': staged_count,
    #     }
    #     orders_log = {
    #         'gid': self.group_id, 'pid': self.id, 'orders': orders
    #     }
    #     hfl.logger.push(hfl.order_count, **count_log)
    #     hfl.logger.push(hfl.orders, **orders_log)
    #     if not len(orders) <= 2:     # this has to hold if all works properly.
    #         self.group.loggy()
    #         raise Exception('something is not right in the orderstore.')
    #     return orders

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

    @atomic
    def update_state(self, message):
        """
        switch between 3 roles (states): out, sniper and maker
        """
        states = {
            'OUT': self._leave_market,
            'SNIPER': self._leave_market,
            'MAKER': self._enter_market,
        }
        old_state = self.status('state')
        new_state = message['state'].upper()
        # update dict that keeps totals for roles
        self.group_stats(old_state, new_state)
        # update player status
        self.status_update('state', new_state)
        try:
            # new state determines the action.
            states[new_state]()
        except KeyError as e:
            log.info(new_state)
            log.info('Player%d: Invalid state update.' % self.id)
       #     raise e
        log_dict = {
                'gid': self.group_id, 'pid': self.id, 'state': new_state
            }
        hfl.events.push(hfl.state_update, **log_dict)
        lablog = prepare(
            group=self.group_id, level='choice', typ='state',
            pid=self.id_in_group, nstate=new_state
        )
        log.experiment(lablog)

    @atomic
    def update_spread(self, message):
        """
        makers can change their spreads
        read new spread
        let all clients know
        replace existing orders with new price
        """
        new_spread = int(message['spread'])
        self.status_update('spread', new_spread)
        # fp  = self.fp()  # what is my fundamental price ?
        # lo, hi = fp - self.spread / 2, fp + self.spread / 2  # then these are legs
        # self.group.broadcast(
        #     ClientMessage.spread_change(self.id_in_group, leg_up=hi, leg_low=lo)
        # )
        log_dict = {'gid': self.group_id, 'pid': self.id, 'spread': new_spread}
        hfl.events.push(hfl.spread_update, **log_dict)
        msgs = self.makers_replace(1)  # replace orders, start from above
        self.group.send_exchange(msgs, delay=True, speed=self.speed)
        lablog = prepare(
            group=self.group_id, level='choice', typ='spread',
            pid=self.id_in_group, nspread=new_spread
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
        new_speed = not self.status('speed')
        self.status_update('speed', new_speed)
        now = labtime()
        if new_speed:
            self.status_update('speed_change_time', now)
        else:
            self._calc_speed_cost(now)
        log_dict = {'gid': self.group_id, 'pid': self.id, 'speed': new_speed}
        hfl.events.push(hfl.speed_update, **log_dict)
        lablog = prepare(
            group=self.group_id, level='choice', typ='speed',
            pid=self.id_in_group, nspeed=new_speed
        )
        log.experiment(lablog)

    def in_market(self, msg):
        log.info('Group%d: Player%d: In market.' % (self.group_id, self.id))
        self.group.players_in_market(self.id)

    def session_finished(self, msg):
        log.info('Group%d: Player%d: Ready to advance.' % (self.group_id, self.id))
        self.subsession.end_trade(self.id)

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
            'role_change': self.update_state,
            'spread_change': self.update_spread,
            'speed_change': self.update_speed,
            'advance_me': self.session_finished,
            'player_ready': self.in_market,
        }
        actions[msg['type']](msg)

    def receive_from_group(self, header, body):
        events= {
            'A': self.handle_enter,
            'U': self.handle_replace,
            'C': self.handle_cancel,
            'E': self.handle_exec,
        }
        events[header](body)
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
        fp  = self.fp()
        spread = self.status('spread')
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
        # orderstore = self.order_store()
        # order = orderstore.get_order(tok)
        # assert order    # I should get rid of these asserts after testing
        # orderstore.activate(stamp, order)
        # orderstore.active[order.token] = order
        # log.info('Group{}: Player{}: Confirm: Enter {}: {}.'.format(
        #     self.group_id, self.id, order.token, order)
        # )
        # self.save_order_store(orderstore)
        current_state = self.status('state')
        # TODO: make base roles point instead of hardcoding
        if current_state == 'MAKER':
            self.makers_broadcast(tok)
        lablog = prepare(
            group=self.group_id, level='exch', typ='enter',
            pid=self.id_in_group, token=order.token, stamp=order.timestamp,
            side=order.side, tif=order.time_in_force, price=order.price
        )
        log.experiment(lablog)

    def _confirm_enter(self, stamp, token):
        """
        orderstore operations when confirm
        """
        orderstore = self.order_store()
        order = orderstore[token]
        if not order:
            log.warning('player %s: order %s not in active orders' % (self.id, labtime(),stamp, token))
    #        raise Exception('order is not in active orders.')
        self.group.loggy()
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
        # orderstore = self.order_store()
        # old_order = orderstore.get_order(ptok)
        # assert old_order
        # new_order = orderstore.get_order(tok)
        # assert new_order
        # orderstore.cancel(stamp, old_order)
        # orderstore.activate(stamp, new_order)
        # orderstore.active[new_order.token] = new_order
        # orderstore.inactive[old_order.token] = old_order
        # self.save_order_store(orderstore)
        current_state = self.status('state')
        if current_state == 'MAKER':
            self.makers_broadcast(token)
        lablog = prepare(
            group=self.group_id, level='exch', typ='replace',
            pid=self.id_in_group, old_token=old_order.token,
            new_token=new_order.token, stamp=new_order.timestamp,
        )
        log.experiment(lablog)


    def _confirm_replace(self, stamp, ptoken, token):
        orderstore = self.order_store()
        old_order = orderstore[ptoken]
        new_order = orderstore[token]
        if not old_order:
            log.warning('player %s: order %s is not in active orders' % (self.id, ptoken))
   #         raise Exception('old order: %s is not in active orders.' % old_order)
        if not new_order:
            log.warning('player %s: order %s is not in active orders.' % (self.id, token))
  #          raise Exception('new order: %s is not in active orders.' % token)
        self.group.loggy()
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
        lablog = prepare(
            group=self.group_id, level='exch', typ='cancel',
            pid=self.id_in_group, token=order.token, stamp=order.timestamp
        )
        log.experiment(lablog)

    def _confirm_cancel(self, stamp, token):
        orderstore = self.order_store()
        order = orderstore[token]
        if not order:
            log.warning('player %s : canceled order %s not found in active orders.', token)
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
        # orderstore = self.order_store()
        # order = orderstore.get_order(tok)
        # orderstore.execute(stamp, order)
        # self.save_order_store(orderstore)
        price = msg['execution_price']
        profit = self.calc_profit(price, order.side, stamp)
        self.group.broadcast(
            client_messages.execution(self.id_in_group, tok, profit)
        )
        lablog = prepare(
            group=self.group_id, level='exch', typ='exec',
            pid=self.id_in_group, token=order.token, price=order.price, 
            stamp=order.timestamp
        )
        log.experiment(lablog)

    def _confirm_exec(self, stamp, token):
        # with cache.lock('key'):
        orderstore = self.order_store()
        order = orderstore[token]
        order = orderstore.inactivate(order, 'executed')
        current_state = self.status('state')
        self.save_order_store(orderstore)
        log_dict = {'gid': self.group_id, 'pid': self.id, 'order': order}
        hfl.events.push(hfl.confirm_exec, **log_dict)
        if current_state == 'MAKER' and order.time_in_force != 0:
            msgs = [self.stage_enter(order.side)]
            self.group.send_exchange(msgs, delay=True, speed=self.speed)
        return order

    def calc_profit(self, exec_price, side, timestamp):
        """
        find the distance btw fundamental and execution prices
        order side determines profit sign
        take speed cost along the way
        """
        fp_key = 'group_fp_' + str(self.group_id)
        fp = cache.get(fp_key).get_FP(timestamp)
        d = abs(fp - exec_price)
        profit = self.status('profit')
        if exec_price < fp:
            # buyer (seller) buys (sells) less than fp
            pi = d if side == 'B' else -d  
        else:
            # seller (buyer) sells (buys) higher than fp
            pi = d if side == 'S' else -d  
        updated_profit = profit + pi
        self.status_update('profit', updated_profit)
        log_dict = {
            'gid': self.group_id, 'pid': self.id, 'amount': pi,
            'side': side, 'profit': updated_profit, 'fp': fp, 
            'p': exec_price,
        }
        hfl.events.push(hfl.profit, **log_dict)
        if self.status('speed'):
            self._calc_speed_cost(labtime())
        lablog = prepare(
            group=self.group_id, level='market', typ='profit',
            source='cross', pid=self.id_in_group, stamp=timestamp,
            endowment=updated_profit, profit=pi
        )
        log.experiment(lablog)
        return pi

    def _calc_speed_cost(self, timestamp):
        """
        calculate speed cost since the previous calculation
        """
        delta = timestamp - self.status('speed_change_time')
        # TODO: move factor to somewhere else.
        nanocost = self.speed_cost * 1e-9
        cost = delta * nanocost
        self.status_update('speed_change_time', timestamp)
        new_profit = self.status('profit') - cost
        self.status_update('profit', new_profit)
        log_dict = {
            'gid': self.group_id, 'pid': self.id,
            'cost': cost, 'delta': delta, 'nanocost': nanocost
        }
        hfl.events.push(hfl.cost, **log_dict)
        lablog = prepare(
            group=self.group_id, level='market', typ='profit',
            source='speed', pid=self.id_in_group, stamp=timestamp,
            endowment=new_profit, profit=-cost
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

    @atomic
    def jump(self, new_price):
        """
        player's response to jump
        update fundamental price
        return jump response to group.jump
        """
        is_positive = new_price - self.fp() > 0.
        self.fp_update(new_price)
        response = False
        current_role = self.status('state')

        if current_role == 'SNIPER':
            side = 'B' if is_positive else 'S'
            order = [self.stage_enter(side, price=self.fp(), time_in_force=0)]
            response = order
        elif current_role == 'MAKER':
            flag = 1 if is_positive else 0
            orders = self.makers_replace(flag)  # makers replace returns 2 ouch messages
            response = orders
        else:
            pass
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


    def order_store(self, init=False):
        """
        player's order store
        lives in cache backend
        """
        k = str(self.id) + '_orders'
        orderstore = None
        if init:
            log.info('Group%d: Player%d: Initialize Order Store.' % (self.group_id, self.id))
            orderstore = OrderStore(self.id, self.id_in_group)
            cache.set(k, orderstore, timeout=None)
            return orderstore
        orderstore = cache.get(k, None)   
        if orderstore is None:
            raise ValueError             
        return orderstore

    # def order_store(self, caller, safe=False, init=False):
    #     """
    #     player's order store
    #     lives in cache backend
    #     """
    #     k = str(self.id) + '_orders'
    #     orderstore = None
    #     if init:
    #         log.info('Group%d: Player%d: Initialize Order Store.' % (self.group_id, self.id))
    #         orderstore = OrderStore(self.id, self.id_in_group)
    #         cache.set(k, orderstore, timeout=None)
    #         return orderstore
    #     c = 0    
    #     if safe:
    #         while cache.delete('lock') == 0: 
    #             time.sleep(0.01)
    #             c += 0.01
    #         log.info('player %s: %d:%s locked orderstore.: %f' % (self.id,labtime(), caller, c))
    #     orderstore = cache.get(k, None)   
    #     log.info('player {} :orders when locked and grabbed. {}:{}'.format(self.id, caller, orderstore))                
    #     return orderstore

    # def order_store(self):
    #     """
    #     player's order store
    #     lives in cache backend
    #     """
    #     k = str(self.id) + '_orders'
    #     order_store = cache.get(k)
    #     if not order_store:
    #         log.info('Group%d: Player%d: Create Order Store.' % (self.group_id, self.id))
    #         order_store = OrderStore(self.id, self.id_in_group)
    #         cache.set(k, order_store, timeout=None)
    #     return order_store

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
                'Group%d: Player%d: Initiate FP as %d .' % (self.group_id, self.id, fp)
            )
            cache.set(k, fp, timeout=None)
        return fp

    def fp_update(self, new_fp):
        k = str(self.id) + '_fp'
        cache.set(k, new_fp, timeout=None)
        # log.info('Group%d: Player%d: Update FP: %d' % (self.group_id, self.id, new_fp))

    def status(self, field):
        k = str(self.id) + '_status'
        status = cache.get(k)
        if not status:
            log.info('Group%d: Player%d: Initiate status dict.' % (self.group_id, self.id))
            status = {
                'state': 'OUT', 'speed': False, 'profit': self.profit,
                'spread': self.spread, 'speed_change_time': 0
            }
            cache.set(k, status, timeout=None)
        out = status[field]
        return out

    def group_stats(self, old_state, new_state):
        k = 'group_stats_' + str(self.group_id)
        group_state = cache.get(k)
        if not group_state:
            group_state = {
                'MAKER': 0, 'SNIPER':0, 'OUT':3
            }
        group_state[old_state] -= 1
        group_state[new_state] += 1
        cache.set(k, group_state, timeout=None)
        total = sum(group_state.values())
        # this is kind of odd to do it here.
        self.group.broadcast(
            client_messages.total_role(group_state)
        )
        assert total == 3

    def status_update(self, field, new_state):
        k = str(self.id) + '_status'
        status = cache.get(k)
        status[field] = new_state
        cache.set(k, status, timeout=None)

class Investor(Model):

    group = ForeignKey(Group)
    order_count = models.IntegerField(initial=1)

    def receive_from_consumer(self, side):
        s = ('Buy' if side=='B' else 'Sell')
        log.info('Group %d: Investor%d: %s.' % (self.group.id, self.order_count, s))
        self.invest(side)

    def invest(self, side):
        p = (2147483647 if side == 'B' else 0)
        order = Order(
            pid= 0, count=self.order_count, status='s', 
            side=side, price=p, time_in_force=0
        )
        ouch = [translate.enter(order)]
        log.debug('Group%d: Investor sends an order: %s' % (self.group.id, order.token))
        self.group.send_exchange([ouch])   # send exchange expects list of lists
        self.order_count += 1
        self.save()
