#!/usr/bin/env python


import logging
from jsonfield import JSONField

from otree.db.models import Model, ForeignKey
from otree.api import ( 
    models, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
)
from otree.models import Session

from django.core.cache import cache

from otree.common_internal import random_chars_8

from .orderstore import OrderStore
from . import utility
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

from . import market_environments

log = logging.getLogger(__name__)

class Constants(BaseConstants):
    name_in_url = 'hft_bcs'
    players_per_group = None
    num_rounds = 3

    short_delay = 0.1
    long_delay = 0.5

    speed_factor = 1e-9
    nasdaq_multiplier = 1e4

    max_ask = 2147483647
    min_bid = 0


class Subsession(BaseSubsession):
    design = models.StringField()
    round_length = models.IntegerField()
    batch_length = models.IntegerField(initial=0)
    code = models.CharField(default=random_chars_8)

    def creating_session(self):
        def create_trade_session(subsession, session_format):
            trade_session_cls = TradeSessionFactory.get_session(session_format)
            trade_session = trade_session_cls(subsession, session_format)
            environment = market_environments.environments[session_format]
            for event_type in environment.exogenous_events:
                filename  = self.session.config[event_type].pop(0)
                trade_session.register_exogenous_event(event_type, filename)
            return trade_session
        session_format = self.session.config['environment']    
        if self.round_number == 1:
            self.session.config = utility.clean_configs(session_format, 
                self.session.config)
            self.session.vars['trade_sessions'] = {} 
        session_configs = self.session.config
        session_format = session_configs['environment']
        session_configs = self.session.config
        trade_session = create_trade_session(self, session_format)
        self.session.vars['trade_sessions'][self.id] = trade_session.id
        exchange_format = session_configs['auction_format']
        exchange_host = session_configs['exchange_host']
        exchange_ports = dict(utility.available_exchange_ports) 
        print(exchange_ports)
        for group in self.get_groups():
            exchange_port = exchange_ports[exchange_format].pop()
            market = trade_session.create_market(exchange_host, exchange_port)
            market.register_group(group, session_configs)
            initialize_market_cache(market)
        utility.configure_model(self, session_format, session_configs)
        initialize_session_cache(trade_session)
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
    market_id = models.StringField()
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
