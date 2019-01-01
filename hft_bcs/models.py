#!/usr/bin/env python


import logging
from datetime import datetime
from jsonfield import JSONField

from .hft_logging.experiment_logger import prepare

from otree.db.models import Model, ForeignKey
from otree.api import (
    models, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
)
from otree.models import Session
from . import client_messages 

from django.core.cache import cache

import time
from . import translator
from .decorators import atomic
from otree.common_internal import random_chars_8
from settings import (
    exp_logs_dir, EXCHANGE_HOST_NO, REAL_WORLD_CURRENCY_CODE )

from .orderstore import OrderStore
from .utility import (process_configs, configure_model, exogenous_event_client,
    available_exchange_ports, exogenous_events, SESSION_FORMAT, EXCHANGES)
from .trader import CDATraderFactory, FBATraderFactory
from .trade_session import TradeSessionFactory
from .market import MarketFactory
from .subject_state import SubjectStateFactory
from .hft_logging.experiment_log import *
from .hft_logging.session_events import log_events
from .hft_logging import row_formatters as hfl
from .exchange import send_exchange
from .cache import (initialize_market_cache, initialize_player_cache, initialize_session_cache,
    get_cache_key, write_to_cache_with_version)


log = logging.getLogger(__name__)

class Constants(BaseConstants):
    name_in_url = 'hft_bcs'
    players_per_group = None
    num_rounds = 3

    short_delay = 0.1   # slow players delay
    long_delay = 0.5    # fast players delay

    exchange_host_label = '{self.subsession.design}_{host}'

    # first_exchange_port = {'CDA': 9001, 'FBA': 9101}  # make this configurable

    speed_factor = 1e-9
    player_state = ('id','id_in_group', 'group_id', 'role', 'fp', 'speed', 'spread', 
        'prev_speed_update', 'code', 'speed_unit_cost', 'exchange_host', 'exchange_port',
        'time_on_speed', 'endowment', 'cost', 'speed_on',
        'market')

    # log file
    log_file = '{dir}{time}_{self.design}_{self.code}_{self.players_per_group}_round_{self.round_number}'

    nasdaq_multiplier = 1e4
    config_fields_to_scale = {
        'fundamental_price':1e4, 
        'initial_spread':1e4,
        'initial_endowment':1e4,
        'speed_cost':1e4,
        'max_spread':1e4
        }

    configs_to_otree_models = {
        'subsession': {
            'players_per_group': 'players_per_group',
            'period_length': 'round_length',
            'auction_format': 'design',
            'batch_length': 'batch_length',
            'trial': 'trial',
            'trial_length': 'trial_length',
        },
        'player': {
            'fundamental_price': 'fp',
            'initial_spread': 'spread',
            'initial_endowment': 'endowment',
            'speed_cost': 'speed_unit_cost',
            'max_spread': 'max_spread',
            'auction_format': 'design',
        }
    }

    max_ask = 2147483647
    min_bid = 0


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

    def creating_session(self):
        def create_trade_session(self):
            trade_session_cls = TradeSessionFactory.get_session(SESSION_FORMAT)
            trade_session = trade_session_cls(self)
            exg_events = exogenous_events[SESSION_FORMAT]
            for e in exg_events:
                filename  = self.session.config[e].pop(0)
                trade_session.register_exogenous_event(e, filename) 
            initialize_session_cache(trade_session)
            return trade_session
        def creating_market(self, exchange_format):
            market_factory = MarketFactory()
            market_cls = market_factory.get_market(SESSION_FORMAT)
            exchange_host = self.session.config['exchange_host']
            global EXCHANGES
            EXCHANGES = available_exchange_ports.copy()
            exchange_port = EXCHANGES[exchange_format].pop()
            market = market_cls()
            market.add_exchange(exchange_host, exchange_port)
            market_data = initialize_market_cache(market)
            return market_data    
        SESSION_FORMAT = self.session.config['environment']
        exchange_format = self.session.config['auction_format']
        if self.round_number == 1:
            self.session.config = process_configs(Constants.config_fields_to_scale, self.session.config)
            global GRIDSIZE
            GRIDSIZE = self.session.config['grid_size']
            if self.has_trial:
                self.is_trial = True
                self.round_length = self.trial_length    
        trade_session = create_trade_session(self)          
        configure_model(self.session.config, Constants.configs_to_otree_models,
            'subsession', self) 
        group_models = self.get_groups()
        for group in group_models:
            market_data = creating_market(self, exchange_format)
            market = market_data['market']
            market.register_session(trade_session.id)
            trade_session.register_market(market.id, market.exchange_address)
            market.register_group(group)
            exchange_host, exchange_port = market.exchange_address
            state_cls = SubjectStateFactory.get_state(SESSION_FORMAT)
            for player in group.get_players():
                player.exchange_host = exchange_host
                player.exchange_port = exchange_port
                player = configure_model(self.session.config, 
                    Constants.configs_to_otree_models, 'player', player)
                subject_state = state_cls.from_otree_player(player)
                initialize_player_cache(player, subject_state, 
                    Constants.player_state)
                player.save()
            market_key = get_cache_key(market.id, 'market')
            write_to_cache_with_version(market_key, market_data, 1)
            group.save()
        session_key = get_cache_key(trade_session.id, 'trade_session')
        cache.set(session_key, trade_session)
        cache.set('trade_session_lock', 'unlocked', timeout=None)
        self.save()
            
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


class Group(BaseGroup):

    pass

class Player(BasePlayer):

    time_on_speed = models.IntegerField(initial=0)
    exchange_host = models.StringField(initial='127.0.0.1')
    exchange_port = models.StringField(initial='9001')
    role = models.StringField(initial='out')
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
    design =  models.CharField()
    consent = models.BooleanField(initial=True)
    inventory = models.IntegerField(initial=0)
    market = models.StringField()
    best_bid = models.IntegerField()
    best_offer = models.IntegerField()
    bid = models.IntegerField()
    offer = models.IntegerField()
    distance_from_bid = models.IntegerField(blank=True)
    distance_from_offer = models.IntegerField(blank=True)
    latent_bid = models.IntegerField(blank=True)
    latent_offer = models.IntegerField(blank=True)
    sliders = models.StringField()
    orderstore = models.StringField(blank=True)


class HFTTraderStateRecord(Model):

    timestamp = models.DateTimeField(auto_now_add=True)
    player_id = models.IntegerField()
    market_id = models.IntegerField()
    role =  models.StringField()
    speed_on = models.BooleanField()
    inventory = models.IntegerField()
    orderstore = models.StringField()
    trigger_event = models.StringField()
    event_message = models.StringField()
    bid = models.IntegerField(blank=True)
    ask = models.IntegerField(blank=True)
