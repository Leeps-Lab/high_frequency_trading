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

from .utility import get_label_as_int, nanoseconds_since_midnight as labtime
from . import exchange
from .profit import Price_Log, Price_Node
from channels import Group as CGroup, Channel
from otree.db.models import Model, ForeignKey
from otree.api import (
    models, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
)
from otree.models import Session
from . import client_messages 
import json
from django.core.cache import cache
from .order import OrderStore
import time
from . import new_translator
from .decorators import atomic
from otree.common_internal import random_chars_8
from settings import (
    exp_logs_dir, EXCHANGE_HOST_NO, REAL_WORLD_CURRENCY_CODE )


from .utility import (scale_configs, from_configs_to_models, exogenous_event_client,
    available_exchange_ports)
from .trader import CDATraderFactory, FBATraderFactory
from .market import MarketFactory
from .subject_state import BCSSubjectState
from .hft_logging.experiment_log import *
from .hft_logging.session_events import log_events
from .hft_logging import row_formatters as hfl
from .exchange import send_exchange
from .event_handlers import process_trader_response, receive_trader_message
from .cache import initialize_market_cache, initialize_player_cache, initialize_session_cache


log = logging.getLogger(__name__)

class Constants(BaseConstants):
    name_in_url = 'hft_bcs'
    players_per_group = None
    num_rounds = 10

    short_delay = 0.1   # slow players delay
    long_delay = 0.5    # fast players delay

    exchange_host_label = '{self.subsession.design}_{host}'

    # first_exchange_port = {'CDA': 9001, 'FBA': 9101}  # make this configurable

    speed_factor = 1e-9
    player_state = ('id','id_in_group', 'group_id', 'role', 'fp', 'speed', 'spread', 'prev_speed_update', 'code', 'speed_unit_cost',
        'exchange_host', 'exchange_port', 'time_on_speed')
    player_accum = ('endowment', 'cost', 'speed_on')
    player_fields = player_state + player_accum

    # group_role_counts = {'OUT': 'players_per_group', 'MAKER': 0, 'SNIPER': 0}

    # cache keys
    # lock_key = '{self.code}_lock'
    # investor_label = 'investors_group_{self.id_in_subsession}_round_{round_number}'
    # jump_label = 'jumps_group_{self.id_in_subsession}_round_{round_number}'
    # player_fp_key = '{self.code}_fp'
    # group_fp_key = 'group_{group_id}_fp'
    # player_orderstore_key = '{self.code}_orders'
    # player_status_key = '{self.code}_status'
    # groups_ready_key = '{self.code}_ready'
    # players_in_market_key  = '{self.code}_in_market'
    # role_count_key = '{self.code}_role_count'
    # player_role_key = '{self.code}_role'

    # unlock_value = 'unlocked'

    # log file
    log_file = '{dir}{time}_{self.design}_{self.code}_{self.players_per_group}_round_{self.round_number}'

    # you may wanna change this if you run otree on different ports.
    # investor_url = 'ws://127.0.0.1:8000/hft_investor/'
    # jump_url = 'ws://127.0.0.1:8000/hft_jump/'

    # investor_py = os.path.join(os.getcwd(), 'hft_bcs/exogenous_event.py')
    # jump_py = os.path.join(os.getcwd(), 'hft_bcs/exogenous_event.py')
    
    nasdaq_multiplier = 1e4
    config_fields_to_scale = {
        'fp':1e4, 
        'spread':1e4,
        'endowment':1e4,
        'speed_unit_cost':1e4,
        'max_spread':1e4
        }

    configs_to_otree_models = {
        'session': {
            'players_per_group': 'players_per_group',
            'round_length': 'session_length',
            'design': 'design',
            'batch_length': 'batch_length',
            'has_trial': 'trial',
            'trial_length': 'trial_length',
        },
        'player': {
            'fp': 'fundamental_price',
            'spread': 'initial_spread',
            'endowment': 'initial_endowment',
            'speed_unit_cost': 'speed_cost',
            'max_spread': 'max_spread',
            'design': 'design'
        }
    }

    # session_field_map = {
    #     'players_per_group': 'players_per_group',
    #     'round_length': 'session_length',
    #     'design': 'design',
    #     'batch_length': 'batch_length',
    #     'has_trial': 'trial',
    #     'trial_length': 'trial_length',
    #     # 'total_rounds': 'num_rounds',
    #     # 'restore_from': 'restore_from',
    #     # 'restore': 'restore',
    #     # 'lambda_i': 'lambda_i',
    #     # 'lambda_j': 'lambda_j',
    # }
    # player_field_map = {
    #     'fp': 'fundamental_price',
    #     'spread': 'initial_spread',
    #     'endowment': 'initial_endowment',
    #     'speed_unit_cost': 'speed_cost',
    #     'max_spread': 'max_spread',
    #     'design': 'design'
    # }
    # player_scaled_fields = ('fp', 'spread', 'endowment', 'speed_unit_cost', 'max_spread')


    #   #   #   #   #   #

    # player_handlers = {
    #     'advance_me': 'session_finished',
    #     'player_ready': 'in_market'
    # }


    #   #   #   #   #   #   #   #   #   #   #


    max_ask = 2147483647
    min_bid = 0
    

    market_events = ('S')
    trader_events = ('spread_change', 'speed_change', 'role_change', 'A', 'U', 'C', 'E')

# subprocesses = {}


# def stop_exogenous(group_id=None):
#     if group_id: 
#         if subprocesses[group_id]:
#             for process in subprocesses[group_id]:
#                 try:
#                     print(group_id)
#                     print(process)
#                     process.kill()
#                 except Exception as e:
#                     log.exception(e)
#     else:
#         for _, process_list in subprocesses.items():
#             if process_list:
#                 for process in process_list:
#                     try:
#                         process.kill()
#                     except Exception as e:
#                         log.exception(e)




class Subsession(BaseSubsession):
    design = models.StringField()
    next_available_exchange = models.IntegerField()
    players_per_group = models.IntegerField()
    round_length = models.IntegerField()
    batch_length = models.IntegerField(initial=0)
    trade_ended = models.BooleanField(initial=False)
    code = models.CharField(default=random_chars_8)
    has_trial = models.BooleanField(initial=True)
    is_trial = models.BooleanField(initial=False)
    trial_length = models.IntegerField(initial=0)
    log_file = models.StringField()
    first_round = models.IntegerField(initial=1)
    last_round = models.IntegerField(initial=0)
    total_rounds = models.IntegerField(initial=0)
    restore_from = models.CharField()
    restore = models.BooleanField(initial=False)
    # lambda_i = models.FloatField()
    # lambda_j = models.FloatField()

    # def init_cache(self):
    #     pairs = {}
    #     session_lock = Constants.lock_key.format(self=self)
    #     pairs[session_lock] = Constants.unlock_value
    #     ready_groups = Constants.groups_ready_key.format(self=self)
    #     pairs[ready_groups] = {g.id: False for g in self.get_groups()}
    #     for k, v in pairs.items():
    #         cache.set(k, v, timeout=None)

    # def convert_lambdas(self):
    #     self.lambda_i = round(1 / self.lambda_i, 1)
    #     self.lambda_j = round(1 / self.lambda_j, 1)
    #     self.save()

    def set_payoff_round(self):
        for player in self.get_players():
            payoff_round = random.randint(self.first_round, self.last_round)
            player.participant.vars['payoff_round'] = payoff_round
            player.save()

    def set_log_file(self):
        now = datetime.now().strftime('%Y-%m-%d_%H-%M')
        log_file = Constants.log_file.format(dir=exp_logs_dir, self=self, time=now)
        self.log_file = log_file
        self.save()

    def assign_groups(self):
        try:
            group_matrix = self.session.config['group_matrix']
        except KeyError:
            raise KeyError('Group assignments not found. You must pass in a list of list.')
        self.set_group_matrix(group_matrix)
        self.save()


    SESSION_FORMAT = None
    EXCHANGES = None

    def creating_session(self):
        def create_trade_session(self):
            
        def creating_market(self, exchange_format):
            market_factory = MarketFactory(SESSION_FORMAT)
            market = market_factory.get_market()
            exchange_host = self.session.config['exchange_host']
            exchange_port = EXCHANGES[exchange_format].pop()
            market.subscribe_exchange(exchange_host, exchange_port)
            initialize_market_cache(market)
            return market         
        SESSION_FORMAT = self.session.config['environment']
  



    def creating_group(self):
        # TODO:this is hardcoded temporarily.
        # self.exch_host =  "127.0.0.1"
  #      self.set_exchange_host()
        # self.exch_port = self.subsession.next_available_exchange
        # self.subsession.next_available_exchange += 1
            # otree wants to create all objects at session start
            # so actual round number is different than Constants.num_rounds
            # default to trial
        rnd = 1 if self.round_number > self.subsession.total_rounds else self.round_number
        investors = Constants.investor_label.format(self=self, round_number=rnd)
        jumps = Constants.jump_label.format(self=self, round_number=rnd)
        self.investor_file = self.session.config[investors]
        self.jump_file = self.session.config[jumps]
        fp = self.session.config['fundamental_price'] * Constants.conversion_factor
        # self.fp_push(fp)
        self.init_cache()
        subprocesses[self.id] = list()
        self.save()
        self.subsession.save()
    def creating_session(self):
        # set session fields
        # for k, v in Constants.session_field_map.items():
        #     setattr(self, k, self.session.config[v])
        # determine if this is a special round
        # trial or last round
        # self.first_round = 1 + self.has_trial
        # self.last_round = self.total_rounds + self.has_trial
        if self.has_trial and self.round_number == 1:
            self.is_trial = True
            self.round_length = self.trial_length
        # set default values for cached session states       
        self.init_cache()
        # set group matrix
        self.assign_groups()
        # set log file
        self.set_log_file()  
        if self.round_number == 1:
            # payoff from a random round will be paid.
            self.set_payoff_round()
        # set the exchange port start
        self.next_available_exchange = Constants.first_exchange_port[self.design]
        groups = self.get_groups()
        for group in groups:
            group.creating_group()
        players = self.get_players()
        # for player in players:
        #     for k, v in Constants.player_field_map.items():
        #         attr = self.session.config[v]
        #         if k in Constants.player_scaled_fields:
        #             attr = attr * Constants.conversion_factor
        #         setattr(player, k, attr)
            player.initialize_cache()
        # s=elf.convert_lambdas()

        #TODO: wtf? make this smaller
        group_players = {g.id: [p.id for p in g.get_players()] for g in groups}
        # l = prepare(group=0, level='header', typ='header', groups=group_players,
        #     session=self.code, design=self.design, initial_spread=players[0].spread,
        #     batch_length=self.batch_length, round_length=self.round_length, round_no=self.round_number)
        # lablog(self.log_file, l)
        self.save()
        self.session.save()

    # def start_trade(self):
    #     log.info('session: starting trade, %d.' % self.round_length)
    #     log_events(subsession=self)
    #     log_events.dump(header=True)
    #     experiment_logger(self.log_file)
    #     for g in self.get_groups():
    #         g.start()  

    # def end_trade(self):      
    #     log.info('session: advancing all players to results page.')
    #     self.trade_ended = True
    #     self.save()
    #     log_events.push(hfl.end)
    #     log_events.dump()
    #     self.session.advance_last_place_participants()

    @atomic
    def groups_ready(self, group_id, action='start'):
        k = Constants.groups_ready_key.format(self=self)
        session_state = cache.get(k)
        session_state[group_id] = True if action == 'start' else False
        cache.set(k, session_state, timeout=None)
        total = sum(session_state.values())
        if total == self.session.num_participants / self.players_per_group:
            self.start_trade()
        if total == 0 and self.trade_ended == False:
            self.end_trade()
  
    def restore_payoffs(self):
        """
        session is otree session objects
        look up db by session_code
        set participants' payoffs equal
        by pairing participant labels
        """
        session_to_restore = Session.objects.get(code=self.restore_from)
        participants = self.session.get_participants()
        old_participants = session_to_restore.get_participants()
        for new_p in participants:
            for old_p in old_participants:
                try:
                    if new_p.label == old_p.label:
                        new_p.payoff = old_p.payoff
                        new_p.save()
                except AttributeError:
                    continue      

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

translator = new_translator.LeepsOuchTranslator()

class Group(BaseGroup):

    exch_host = models.StringField()
    exch_port = models.IntegerField()
    investor_file = models.StringField()
    jump_file = models.StringField()
    is_trading = models.BooleanField(initial=False)
    code = models.CharField(default=random_chars_8)
    log_file = models.StringField()

    # def init_cache(self):
    #     pairs = {}
    #     group_lock = Constants.lock_key.format(self=self)
    #     pairs[group_lock] = Constants.unlock_value
    #     in_market_key= Constants.players_in_market_key.format(self=self)   
    #     pairs[in_market_key] = {p.id: False for p in self.get_players()}
    #     role_count_key = Constants.role_count_key.format(self=self)
    #     pairs[role_count_key] = {k: getattr(self.subsession, v) if isinstance(v, str) else v
    #                                 for k, v in Constants.group_role_counts.items()} 
    #     for k, v in pairs.items():
    #         cache.set(k, v, timeout=None)

    def creating_group(self):
        # TODO:this is hardcoded temporarily.
        self.exch_host =  "127.0.0.1"
  #      self.set_exchange_host()
        self.exch_port = self.subsession.next_available_exchange
        self.subsession.next_available_exchange += 1
            # otree wants to create all objects at session start
            # so actual round number is different than Constants.num_rounds
            # default to trial
        rnd = 1 if self.round_number > self.subsession.total_rounds else self.round_number
        investors = Constants.investor_label.format(self=self, round_number=rnd)
        jumps = Constants.jump_label.format(self=self, round_number=rnd)
        self.investor_file = self.session.config[investors]
        self.jump_file = self.session.config[jumps]
        fp = self.session.config['fundamental_price'] * Constants.conversion_factor
        # self.fp_push(fp)
        self.init_cache()
        subprocesses[self.id] = list()
        self.save()
        self.subsession.save()

    # TODO: we will add some buttons to 
    # session monitor page and trigger 
    # each of these events from the admin page
    # def start(self):
    #     # self.spawn(
    #     #     Constants.investor_py,
    #     #     Constants.investor_url,
    #     #     self.investor_file
    #     # )
    #     # self.spawn(
    #     #     Constants.jump_py,
    #     #     Constants.jump_url,
    #     #     self.jump_file
    #     # )
    #     self.connect_to_exchange()
    #     self.start_exchange()
    #     self.broadcast(
    #         client_messages.start_session()
    #     )
    #     log_events.push(hfl.start, **{'gid': self.id})
    #     experiment_logger.log(StartLog(model=self))
    #     self.is_trading = True
    #     self.save()

    # @atomic
    # def end_trade(self, player_id):
    #     if self.is_trading == True:
    #         log.info('Group%d: Player%d flags session end.' % (self.id, player_id))
    #         stop_exogenous(group_id=self.id)
    #         self.disconnect_from_exchange()
    #         self.loggy()
    #         self.is_trading = False                                                                                                                                                     
    #         self.save()
    #         experiment_logger.log(EndLog(model=self))
    #         self.subsession.groups_ready(self.id, action='end')
    #     else:
    #         pass

    # def start_exchange(self):
    #     """
    #     sends a system start message
    #     to the exchange to allow trade
    #     """
    #     start_ouch = translate.system_start('S')
    #     self.send_exchange(start_ouch)
    #     log_events.push(hfl.exchange, **{'gid': self.id, 'context': 'sent system start message'})

    # def connect_to_exchange(self):
    #     try:
    #         exchange.connect(self, self.exch_host, self.exch_port, wait_for_connection=True)
    #     except ValueError as e:
    #         log.warning(e)

    def disconnect_from_exchange(self):
        exchange.disconnect(self, self.exch_host, self.exch_port)

    # def send_exchange(self, msgs, delay=False, speed=False):
    #     """
    #     msgs is a list of lists
    #     """
    #     msgs_flat = [m for msg in msgs for m in msg]
    #     true_msgs = filter(lambda x: x is not False, msgs_flat)
    #     if delay:
    #         dur = Constants.short_delay if speed else Constants.long_delay
    #     else:
    #         dur = 0.
    #     conn = exchange.connect(self, self.exch_host, self.exch_port).connection
    #     for m in true_msgs:
    #         conn.sendMessage(m, dur)
    
    # def receive_from_exchange(self, msg):
    #     """
    #     handles messages coming from the exchange
    #     finds the relevant player for
    #     passes on message the player
    #     also logs investor executions
    #     """
    #     msg_type, fields = translator.decode(msg)
    #     if msg_type == 'S':
    #         event = fields['event_code']
    #         if event in ['B', 'P']:
    #             log_events.push(hfl.batch, **{'gid': self.id})
    #             self.broadcast(client_messages.batch(event=event))
    #         return
    #     token = fields.get('order_token')
    #     if token is None:
    #         token = fields.get('replacement_order_token')
    #     subject = token[3]
    #     # index 3 is subject ID
    #     if subject == '@':
    #         if msg_type == 'E':
    #             # log investor execution
    #             log_events.push(hfl.inv_trans, **{'gid': self.id, 'token': token})
    #         else:
    #             # we really do not care about
    #             # investor confirm at this point.
    #             pass
    #     else:
    #         pid = ord(subject) - 64
    #         # TODO: we should find a way to not make
    #         # this db call, it takes ages.
    #         player = self.get_player_by_id(pid)
    #         try:
    #             print(fields)
    #             trader = receive_trader_message(player.id, player.design, msg_type, **fields)
    #             process_trader_response(trader.outgoing_exchange_messages, trader.outgoing_broadcast_messages)
    #         except Exception as e:
    #             log.exception(e)


    # def broadcast(self, note):
    #     """
    #     broadcast via channel layer
    #     """
    #     message = json.dumps(note)
    #     CGroup(str(self.id)).send({"text": message})

    # def spawn(self, name, url, data):
    #     """
    #     fires exogenous investors and jumps
    #     as subprocesses
    #     """
    #     cmd = ['python', name, str(self.id), url, data]
    #     p = subprocess.Popen(cmd)
    #     try:
    #         subprocesses[self.id].append(p)
    #     except KeyError as e:
    #         log.exception(e)
    #         subprocesses[self.id] = []
    #         subprocesses[self.id].append(p)
    #     print(subprocesses)
    #     log.debug('Group%d: Fire %s.' % (self.id, name))

    # def jump_event(self, msg):
    #     """
    #     this is the fundamental price jump
    #     let all client know the new price
    #     get automated responses
    #     randomize and send to exchange
    #     """
    #     new_price = int(msg['size'])
    #     # self.fp_push(new_price)
    #     # broadcast new price to clients
    #     self.broadcast(client_messages.fp_change(new_price))
    #     players = self.get_players()
    #     # each player will respond to the
    #     # new fundamental price information.
    #     log.debug('Group%d: jump to %d !!' % (self.id, new_price))
    #     log_events.push(hfl.jump, **{'gid': self.id, 'np': new_price})        
    #     responses = [p.jump(new_price) for p in players]
    #     # then we shuffle responses and send to the exchange
    #     # index 1 is an orders list of list
    #     true_responses = list(filter(lambda x: x[1] is not False, responses))
    #     random.shuffle(true_responses)
    #     # index 2 is speed bool
    #     for r in true_responses:
    #         orders, speed = r[1], r[2]
    #         if orders:
    #             self.send_exchange(orders, delay=True, speed=speed)
    #     for speed in True, False:
    #         # index 0 is the player id
    #         move_order = [r[0] for r in true_responses if r[2] is speed]
    #         log_events.push(hfl.move_order, **{'gid': self.id, 'speed':speed, 'move_order': move_order})
    #     # this is here since we are still debugging,
    #     self.loggy()


    # @atomic
    # def players_in_market(self, player_id):
    #     k = Constants.players_in_market_key.format(self=self)
    #     players_in_market = cache.get(k)
    #     players_in_market[player_id] = True
    #     cache.set(k, players_in_market, timeout=None)
    #     total = sum(players_in_market.values())
    #     if self.subsession.players_per_group == total:
    #         log.info('Group%d: all players are in market.' % self.id)
    #         self.subsession.groups_ready(self.id)
    #     else:
    #         log.debug('Group%d: %d players are in market.' % (self.id, total))
    
    # @atomic
    # def group_stats(self, old_state, new_state):
    #     k = Constants.role_count_key.format(self=self)
    #     group_state = cache.get(k)
    #     ppg = self.subsession.players_per_group
    #     group_state[old_state] -= 1
    #     group_state[new_state] += 1
    #     cache.set(k, group_state, timeout=None)
    #     total = sum(group_state.values())
    #     self.broadcast(
    #         client_messages.total_role(group_state)
    #     )
    #     if total != ppg:
    #         raise ValueError('total: %d, ppg: %d' % (total, ppg))

    def loggy(self):
        log_events.convert()
        log_events.dump()


class Player(BasePlayer):

    time_on_speed = models.IntegerField(initial=0)
    exchange_host = models.StringField(initial='127.0.0.1')
    exchange_port = models.StringField(initial='9001')
    role = models.StringField(initial='OUT')
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
    design =  models.CharField()
    consent = models.BooleanField(initial=True)
    final_payoff = models.IntegerField()
    total_payoff = models.IntegerField()
    inventory = models.IntegerField(initial=0)

    def from_subject_state(self, subject_state):
        raise NotImplementedError()

 
#   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #

    # @atomic
    # def jump(self, price):
    #     response = None
    #     trader = self.get_trader()
    #     orders = trader.jump(price)
    #     self.save_trader(trader)
    #     response = (trader.id, orders, trader.speed)
    #     return response

    # # Client actions

    # def in_market(self, **kwargs):
    #     log.debug('Group%d: Player%d: In market.' % (self.group_id, self.id))
    #     self.group.players_in_market(self.id)

    # def session_finished(self, **kwargs):
    #     log.debug('Group%d: Player%d: Ready to advance.' % (self.group_id, self.id))
    #     if self.subsession.trade_ended == False:
    #         self.group.end_trade(self.id)

    # Receive methods
    # action starts here
   

    def take_cost(self):
        now = labtime()
        trader = self.get_trader()
        trader.take_cost(now)
        self.save_trader(trader)
    
    def do_payoff(self):
        trader = self.get_trader()
        profit, cost, payoff = trader.do_payoff()
        self.save_trader(trader)
        return payoff

# class Investor(Model):

#     group = ForeignKey(Group)
#     order_count = models.IntegerField(initial=1)

#     def receive_from_consumer(self, msg):
#         side = msg['direction']
#         s = ('buy' if side=='B' else 'sell')
#         log.debug('Group%d: investor%d: %s.' % (self.group.id, self.order_count, s))
#         # self.invest(side)

# #     # def invest(self, side):
#     #     p = (2147483647 if side == 'B' else 0)
#     #     # order = Order(
#     #     #     pid= 0, count=self.order_count, status='stage', 
#     #     #     side=side, price=p, time_in_force=self.group.subsession.batch_length  # LOL
#     #     # )
#     #     ouch = [translate.enter(order)]
#     #     self.group.send_exchange([ouch])   # send exchange expects list of lists
#     #     self.order_count += 1
#     #     self.save()
