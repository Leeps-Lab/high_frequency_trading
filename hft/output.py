from otree.api import models
from otree.db.models import Model, ForeignKey
import datetime
import os
import csv
import json
import logging
from .cache import get_cache_key
from django.core.cache import cache

log = logging.getLogger(__name__)

exported_player_fields = ('wealth', 'cash', 'technology_cost', 'role', 
    'speed_on', 'time_on_speed', 'inventory', 'order_imbalance', 'reference_price'
    'bid', 'offer', 'best_bid', 'best_offer', 'target_bid',
    'target_offer', 'implied_bid', 'implied_offer', 'slider_a_x',
    'slider_a_y')

class HFTPlayerStateRecord(Model):

    csv_headers = ('timestamp', 'subsession_id', 'market_id', 'player_id', 'trigger_event_type',
        'event_no') + exported_player_fields

    timestamp = models.DateTimeField(auto_now_add=True)
    subsession_id = models.StringField()
    player_id = models.IntegerField()
    market_id = models.StringField()
    wealth = models.IntegerField()
    cash = models.IntegerField()
    technology_cost = models.IntegerField(initial=0)
    role =  models.StringField()
    speed_on = models.BooleanField()
    time_on_speed = models.IntegerField()
    trigger_event_type = models.StringField()
    event_no = models.IntegerField()
    inventory = models.IntegerField()
    orderstore = models.StringField()
    bid = models.IntegerField(blank=True)
    offer = models.IntegerField(blank=True)
    best_bid = models.IntegerField(blank=True)
    best_offer = models.IntegerField(blank=True)
    target_bid = models.IntegerField(blank=True)
    target_offer = models.IntegerField(blank=True)
    implied_bid = models.IntegerField(blank=True)
    implied_offer = models.IntegerField(blank=True)
    slider_a_x = models.FloatField(blank=True)
    slider_a_y = models.FloatField(blank=True)
    order_imbalance = models.FloatField(blank=True)
    reference_price = models.FloatField(blank=True)

    def from_event_and_player(self, event_dict, player):
        for field in exported_player_fields + ('orderstore'):
            setattr(self, field, getattr(player, field))  
        self.player_id = int(player.id)
        self.trigger_event_type = str(event_dict['type'])  
        self.event_no = int(event_dict['reference_no'])
        self.subsession_id = str(event_dict['subsession_id'])
        return self

class HFTPlayerSessionSummary(Model):
    subsession_id = models.StringField()
    player_id = models.IntegerField()
    market_id = models.StringField()
    imbalance_sensitivity = models.FloatField()
    inventory_sensitivity = models.FloatField()
    time_as_maker = models.FloatField()
    time_as_out = models.FloatField()
    time_as_taker = models.FloatField()
    time_as_manual = models.FloatField()
    wealth = models.IntegerField()

def state_for_results_template(player):
    summary_objects = HFTPlayerSessionSummary.objects.filter(subsession_id=player.subsession.id, 
        market_id=player.market_id)
    payoffs = {str(o.player_id): int(o.wealth * 0.0001) for o in summary_objects}
    names = {str(o.player_id): 'You' if o.player_id == player.id else 'Anonymous Trader' 
        for o in summary_objects}
    strategies = {str(o.player_id): {'maker': o.time_as_maker, 'taker': o.time_as_taker,
        'manual': o.time_as_manual, 'out': o.time_as_out} for o in summary_objects}
    inv_sensitivies = {str(o.player_id): o.inventory_sensitivity for o in summary_objects}
    imbalance_sensitivies = {str(o.player_id): o.imbalance_sensitivity for o in summary_objects}
    return {'payoffs': payoffs, 'names': names, 'strategies': strategies, 
        'inv_sens': inv_sensitivies, 'imb_sens': imbalance_sensitivies}

def elo_player_summary(player):
    market = cache.get(get_cache_key(player.market_id, 'market'))['market']
    session_length = market.session_end - market.session_start
    average_sens = _get_average_sensitivies(player.subsession.id, player.market_id, player.id,
        market.session_start, market.session_end)
    session_length_seconds = session_length.seconds
    percent_per_role = _calculate_role_time_percentage(market.role_group, player.id,
        session_length_seconds)
    summary_object = HFTPlayerSessionSummary(subsession_id=player.subsession.id, 
        market_id=player.market_id,
        player_id=player.id, 
        imbalance_sensitivity=average_sens['slider_a_x'],
        inventory_sensitivity=average_sens['slider_a_y'], 
        time_as_maker=percent_per_role['maker'],
        time_as_taker=percent_per_role['taker'], 
        time_as_out=percent_per_role['out'],
        time_as_manual=percent_per_role['manual'], 
        wealth=player.cash)
    summary_object.save()

def _get_average_sensitivies(subsession_id, market_id, player_id, session_start,
    session_end, default=0):
    session_duration = session_end - session_start
    session_duration = session_duration.seconds
    player_state_records = HFTPlayerStateRecord.objects.filter(subsession_id=subsession_id,
        market_id=market_id, player_id=player_id, trigger_event_type='slider').order_by('-timestamp')
    slider_durations = {}
    for slider_name in ('slider_a_x', 'slider_a_y'):
        previous_slider_change_at = session_start
        current_slider_value = default 
        slider_values = {current_slider_value: 0}
        for each in player_state_records:
            new_slider_value = getattr(each, slider_name)
            if new_slider_value != current_slider_value:
                slider_values[new_slider_value] = 0
                duration = each.timestamp - previous_slider_change_at
                duration = duration.seconds
                slider_values[current_slider_value] += duration
                current_slider_value = new_slider_value
                previous_slider_change_at = each.timestamp
        closing_timedelta = session_end - previous_slider_change_at
        slider_values[current_slider_value] += closing_timedelta.seconds
        slider_durations[slider_name] = slider_values  
    slider_averages = {}
    for slider_name in ('slider_a_x', 'slider_a_y'):
        slider_values = slider_durations[slider_name]
        denum = sum(k for k in slider_values.values())
        num = sum(k * v for k, v in slider_values.items())
        slider_averages[slider_name] = round(num / denum, 1)
    return slider_averages 

def _calculate_role_time_percentage(market_role_group, player_id, session_length):
    duration_per_role = {}
    for role_name in market_role_group.role_names:
        tracked_role = getattr(market_role_group, role_name)
        try:
            duration_per_role[role_name] = tracked_role.time_spent_per_player[player_id]
        except KeyError:
            duration_per_role[role_name] = 0
    total_time_in_session = sum(duration_per_role.values())
    if total_time_in_session == 0:
        raise ValueError('total time in session is 0 for player {}'.format(player_id))
    normal_dur_per_role = {k: round(v / total_time_in_session, 2) for k, v in duration_per_role.items()}
    return normal_dur_per_role

class HFTEventRecord(Model):

    csv_headers = ['event_no','timestamp', 'subsession_id', 'market_id', 
        'event_source', 'event_type', 'original_message', 'attachments', 'outgoing_messages']
    
    subsession_id= models.StringField()
    market_id = models.StringField()
    timestamp = models.DateTimeField(auto_now_add=True)
    event_no = models.IntegerField()
    event_source = models.StringField()
    event_type = models.StringField()
    original_message = models.StringField()
    attachments = models.StringField()

    def from_event(self, event_dict):
        self.subsession_id = str(event_dict['subsession_id'])
        self.market_id = str(event_dict['market_id'])
        self.event_no = int(event_dict['reference_no'])
        self.event_type = str(event_dict['type'])
        self.event_source = str(event_dict['event_source'])
        self.all_keys = str(event_dict)
        return self


class HFTInvestorRecord(Model):

    csv_headers = ['timestamp', 'exchange_timestamp', 'subsession_id', 
        'market_id', 'status', 'buy_sell_indicator', 'price', 'order_token']

    timestamp = models.DateTimeField(auto_now_add=True)
    exchange_timestamp = models.BigIntegerField()
    subsession_id= models.StringField()
    market_id = models.StringField()
    order_token = models.StringField()
    status = models.StringField()
    buy_sell_indicator = models.StringField()
    price = models.IntegerField()

    def from_event(self, event):
        self.subsession_id = str(event_dict['subsession_id'])
        self.market_id = str(event_dict['market_id'])       
        self.status = event.event_type
        self.order_token = event.message.data.order_token
        if 'buy_sell_indicator' in event.message.data:
            self.buy_sell_indicator = event.message.data.buy_sell_indicator
        else:
            self.buy_sell_indicator = event.message.data.order_token[4]
        if 'price' in event.message:
            self.price = event.message.data.price
        else:
            self.price = event.message.data.execution_price
        self.exchange_timestamp = event.message.data.timestamp
        return self

def _elo_fields(player, subject_state):
    for field in exported_player_fields + 'orderstore':
        if hasattr(subject_state, field):
            value = getattr(subject_state, field)
            if value is not None:
                setattr(player, field, value)
    if subject_state.sliders is not None:
        player.slider_a_x = float(subject_state.sliders.a_x)
        player.slider_a_y = float(subject_state.sliders.a_y)
    player.inventory = int(subject_state.orderstore.inventory)
    player.orderstore = str(subject_state.orderstore)
    player.bid = subject_state.orderstore.bid
    player.offer = subject_state.orderstore.offer
    player.market_id = str(subject_state.market_id)

def from_trader_to_player(player, subject_state, post=_elo_fields):
    for field in subject_state.__slots__:
        if hasattr(player, field):
            setattr(player, field, getattr(subject_state, field))
    if post:
        post(player, subject_state)
    player.save()
    return player