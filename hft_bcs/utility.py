import time
import numpy as np
import datetime
import pytz
import logging
import os 
from .cache import get_cache_key
from django.core.cache import cache

log = logging.getLogger(__name__)

DEFAULT_TIMEZONE = pytz.timezone('US/Pacific')

exogenous_events = {
    'BCS': ['investor_arrivals', 'fundamental_value_jumps'],
    'LEEPS': ['investor_arrivals']
}  
market_events = ('S', 'player_ready', 'advance_me')
trader_events = ('spread_change', 'speed_change', 'role_change', 'A', 'U', 'C', 'E')

exogenous_event_endpoints = {
    'investor_arrivals': 'ws://127.0.0.1:8000/hft_investor/{subsession_id}',
    'fundamental_value_jumps': 'ws://127.0.0.1:8000/hft_jump/{subsession_id}'
}

exogenous_event_client = 'hft_bcs/exogenous_event_client.py'

available_exchange_ports = {
    'CDA': list(range(9010, 9000, -1)),
    'FBA': list(range(9110, 9100, -1)),
    'IEX': list(range(9210, 9200, -1))
}

ouch_fields = ('price', 'time_in_force', 'display', 'buy_sell_indicator')

MAX_ASK = 2147483647
MIN_BID = 0

def format_message(message_type, **kwargs):
    message = {'message_type': message_type, 'payload': {} }
    for k, v in kwargs.items():
        message['payload'][k] = v
    return message

def process_configs(scaling_map, session_configs):
    adjusted_configs = dict(session_configs)
    for k, v in session_configs.items():
        try:
            adjusted_configs[k] = v * scaling_map[k]
        except KeyError:
            pass
    return adjusted_configs
        
def configure_model(configs:dict, mapping:dict, model_type, model):
    """
    map configs to database models
    """    
    pairs = mapping[model_type] 
    for k, v in pairs.items():
        config_value = configs[k]
        setattr(model, v, config_value)
    return model

def pretranslate_hacks(message_type, message_data):
    if message_type == 'replace':
        message_data['price'] = message_data['replace_price']
    return message_data

def nanoseconds_since_midnight(tz=DEFAULT_TIMEZONE):
    now = datetime.datetime.now(tz=tz)
    timestamp = 0  # since midnight
    timestamp += now.hour
    timestamp *= 60  # hours -> minutes
    timestamp += now.minute
    timestamp *= 60  # minutes -> seconds
    timestamp += now.second
    timestamp *= 10**6  # seconds -> microsecnds
    timestamp += now.microsecond
    timestamp *= 10**3  # microseconds -> nanoseconds
    return timestamp

def leeps_fields(player, subject_state):
    player.best_bid = subject_state.best_quotes['bid']
    player.best_offer = subject_state.best_quotes['offer']
    if subject_state.distance_from_best_quote is not None:
        player.distance_from_bid = subject_state.distance_from_best_quote['bid']
        player.distance_from_offer = subject_state.distance_from_best_quote['offer']
    if subject_state.latent_quote is not None:
        lb, lo = subject_state.latent_quote
        player.latent_bid = lb
        player.latent_offer = lo
    if subject_state.sliders is not None:
        player.sliders = str(subject_state.sliders)
    player.orderstore = str(subject_state.orderstore)
    player.bid = subject_state.orderstore.bid
    player.ask = subject_state.orderstore.ask


def kwargs_from_event(event):
    kwargs = event.message.copy()
    for k, v in event.attachments.items():
        if k not in kwargs and v is not None:
            kwargs[k] = v
    return kwargs

def from_trader_to_player(player_id, subject_state, post=leeps_fields):
    player_key = get_cache_key(subject_state.id, 'player')
    player = cache.get(player_key)['model']
    for field in subject_state.__slots__:
        if hasattr(player, field):
            setattr(player, field, getattr(subject_state, field))
    if post:
        post(player, subject_state)
    player.save()
    return player


