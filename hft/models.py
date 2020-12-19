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
from . import utility
from .trader import TraderFactory
from .trade_session import TradeSessionFactory
from .market import MarketFactory
from .cache import initialize_model_cache, set_market_id_table, get_market_id_table
from .exogenous_event import ExogenousEventModelFactory
from . import market_environments
from django.utils import timezone

from .dispatcher import DispatcherFactory


log = logging.getLogger(__name__)

class Constants(BaseConstants):
    name_in_url = 'hft'
    players_per_group = None
    num_rounds = 1


class Subsession(BaseSubsession):
    model_name = models.StringField(initial='subsession')
    auction_format = models.StringField()
    session_duration = models.IntegerField()
    batch_length = models.IntegerField(initial=0)
    code = models.CharField(default=random_chars_8)

    def creating_session(self):
        def create_trade_session(session_format):
            trade_session_cls = TradeSessionFactory.get_session(session_format)
            dispatcher = DispatcherFactory.get_dispatcher(session_format)
            trade_session = trade_session_cls(self, session_format, dispatcher)
            environment = market_environments.environments[session_format]
            for event_type in environment.exogenous_events:
                event_filename = self.session.config[event_type].pop(0)
                trade_session.register_exogenous_event(
                    event_type, event_filename)
            return trade_session
        session_format = self.session.config['environment']    
        if self.round_number == 1:
            self.session.config = utility.process_configs(
                session_format, self.session.config)
            self.do_groups()
        else:
            self.group_like_round(1)
        session_configs = self.session.config
        session_format = session_configs['environment']
        trade_session = create_trade_session(session_format)
        self.auction_format = session_configs['auction_format']
        exchange_host = session_configs['matching_engine_host']
        all_exchange_ports = copy.deepcopy(utility.available_exchange_ports)
        market_id_map = {}
        for group in self.get_groups():
            group_id = group.id
            exchange_port = all_exchange_ports[self.auction_format].pop()
            market = trade_session.create_market(
                group_id, exchange_host, exchange_port, **session_configs)                                 
            for player in group.get_players():
                market.register_player(player)
                player.configure_for_trade_session(market, session_format)
                trader = TraderFactory.get_trader(session_format, player)
                initialize_model_cache(trader)
            initialize_model_cache(market)
            market_id_map[market.id_in_subsession] = market.market_id
            for event_type_name in trade_session.exogenous_events.keys():
                exogenous_event_manager_model = ExogenousEventModelFactory.get_model(
                    event_type_name, market)
                if exogenous_event_manager_model:
                    initialize_model_cache(exogenous_event_manager_model)
        set_market_id_table(trade_session.subsession_id, market_id_map)
        self.configure_for_trade_session(session_format)
        initialize_model_cache(trade_session)
        self.save()


    def configure_for_trade_session(self, session_format: str):
        utility.configure_model_for_market('subsession', self, session_format,
            self.session.config)
        self.save()

    def do_groups(self):
        # set groups as suggested in oTree docs.
        group_matrix = []
        players = self.get_players()
        ppg = self.session.config['players_per_group']
        for i in range(0, len(players), ppg):
            group_matrix.append(players[i:i+ppg])
        self.set_group_matrix(group_matrix)
            
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

    channel = models.CharField(max_length=255)
    consented = models.BooleanField(initial=False)
    exchange_host = models.CharField()
    exchange_port = models.IntegerField()
    # subsession_id = models.CharField()
    market_id = models.CharField()
    id_in_market = models.IntegerField()
    speed_unit_cost = models.IntegerField()
    net_worth = models.IntegerField()
    cash = models.IntegerField()
    cost = models.IntegerField()
    speed_cost = models.IntegerField()
    tax_paid = models.IntegerField()
    reference_price = models.IntegerField()
    inventory = models.IntegerField()
    bid = models.IntegerField()
    offer = models.IntegerField()
    staged_bid = models.IntegerField()
    staged_offer = models.IntegerField()
    implied_bid = models.IntegerField()
    implied_offer = models.IntegerField()
    best_bid = models.IntegerField()
    best_offer = models.IntegerField()
    e_best_bid = models.IntegerField()
    e_best_offer = models.IntegerField()
    slider_a_x = models.FloatField()
    slider_a_y = models.FloatField()
    slider_a_z = models.FloatField()
    signed_volume = models.FloatField()
    e_signed_volume = models.FloatField()

    # fields for this player's initial strategy decisions
    # these are set from the InitialDecisionSelection form
    initial_slider_a_x = models.FloatField()
    initial_slider_a_y = models.FloatField()
    initial_slider_a_z = models.FloatField()
    initial_role = models.CharField()
    initial_speed_on = models.BooleanField()

    def configure_for_trade_session(self, market, session_format: str):
        for field in ('exchange_host', 'exchange_port', 'market_id', 'subsession_id'):
            setattr(self, field, getattr(market, field))
        utility.configure_model_for_market('player', self, session_format, 
                                           self.session.config)
        self.save()
    
    def update_from_state_record(self, state_record):
        for field in state_record._meta.fields:
            if hasattr(self, field.name):
                attr = getattr(self, field.name)
                if attr is None:
                    setattr(self, field.name, getattr(state_record, field.name))
        self.save()

