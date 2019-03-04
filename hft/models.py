#!/usr/bin/env python


import logging
from jsonfield import JSONField

from otree.db.models import Model, ForeignKey
from otree.api import ( 
    models, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
)
from otree.models import Session

from django.core.cache import cache
import copy
from otree.common_internal import random_chars_8

from .orderstore import OrderStore
from . import utility
from .trader import CDATraderFactory, FBATraderFactory
from .trade_session import TradeSessionFactory
from .market import MarketFactory
from .subject_state import SubjectStateFactory
from .exchange import send_exchange
from .cache import (initialize_market_cache, initialize_player_cache, initialize_session_cache,
    initialize_investor_cache, get_cache_key, write_to_cache_with_version, set_market_id_map,
    get_market_id_map)
from .investor import InvestorFactory

from . import market_environments

log = logging.getLogger(__name__)

class Constants(BaseConstants):
    name_in_url = 'hft'
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
            self.session.config = utility.type_check_configs(session_format, 
                self.session.config)
            self.session.config = utility.scale_configs(session_format, 
                self.session.config)
            self.session.vars['trade_sessions'] = {} 
        session_configs = self.session.config
        session_format = session_configs['environment']
        trade_session = create_trade_session(self, session_format)
        self.session.vars['trade_sessions'][self.id] = trade_session.subsession_id
        exchange_format = session_configs['auction_format']
        exchange_host = session_configs['exchange_host']
        all_exchange_ports = copy.deepcopy(utility.available_exchange_ports)
        market_id_map = {}
        for group in self.get_groups():
            exchange_port = all_exchange_ports[exchange_format].pop()
            market = trade_session.create_market(exchange_host, exchange_port)
            for player in group.get_players():
                market.register_player(group.id, player.id)
                player.configure_for_trade_session(exchange_host, exchange_port, 
                    market.market_id, session_format)
                trader_state_cls = market.state_factory.get_state(session_format)
                trader_initial_state = trader_state_cls.from_otree_player(player)
                initialize_player_cache(player, trader_initial_state)
            initialize_market_cache(market)
            market_id_map[market.id_in_subsession] = market.market_id
            if 'investor_arrivals' in trade_session.exogenous_events.keys():
                investor = InvestorFactory.get_investor(session_format, market.subsession_id,
                    market.market_id, exchange_host, exchange_port)
                initialize_investor_cache(investor)
        set_market_id_map(trade_session.subsession_id, market_id_map)
        self.configure_for_trade_session(session_format)
        initialize_session_cache(trade_session)
        cache.set('trade_session_lock', 'unlocked', timeout=None)
        self.save()
    
    def configure_for_trade_session(self, session_format:str):
        utility.configure_model_for_market('subsession', self, session_format,
            self.session.config)
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

    consented = models.BooleanField(initial=True)
    exchange_host = models.StringField(initial='127.0.0.1')
    exchange_port = models.IntegerField()
    role = models.StringField(initial='out')
    channel = models.CharField(max_length=255)
    cost = models.IntegerField(initial=0)
    technology_cost = models.IntegerField(initial=0)
    cash = models.IntegerField(initial=0)
    wealth = models.IntegerField(initial=0)
    speed_on = models.IntegerField(initial=0)
    time_on_speed = models.IntegerField(initial=0)
    technology_unit_cost = models.IntegerField(initial=0)
    design =  models.CharField()
    inventory = models.IntegerField(initial=0)
    market_id = models.StringField()
    best_bid = models.IntegerField()
    best_offer = models.IntegerField()
    bid = models.IntegerField()
    offer = models.IntegerField()
    target_bid = models.IntegerField(blank=True)
    target_offer = models.IntegerField(blank=True)
    sliders = models.StringField()
    orderstore = models.StringField(blank=True)
    implied_bid = models.IntegerField(blank=True)
    implied_offer = models.IntegerField(blank=True)
    slider_a_x = models.DecimalField(decimal_places=2, max_digits=4, blank=True)
    slider_a_y = models.DecimalField(decimal_places=2, max_digits=4, blank=True)
    order_imbalance = models.DecimalField(decimal_places=2, max_digits=4, blank=True)
    reference_price = models.DecimalField(decimal_places=2, max_digits=4, blank=True)

    def configure_for_trade_session(self, exchange_host:str, exchange_port:int, 
        market_id:str, session_format:str):
        self.exchange_host = exchange_host
        self.exchange_port = exchange_port
        self.market_id = market_id
        utility.configure_model_for_market('player', self, session_format, self.session.config)
        self.save()
