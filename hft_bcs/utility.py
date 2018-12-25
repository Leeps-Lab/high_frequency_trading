import time
import numpy as np
import datetime
import pytz
import logging
import os 

log = logging.getLogger(__name__)

DEFAULT_TIMEZONE = pytz.timezone('US/Pacific')

exogenous_events = {
    'BCS': ['investor_arrivals', 'fundamental_value_jumps']
}  
market_events = ('S', 'player_ready', 'advance_me')
trader_events = ('spread_change', 'speed_change', 'role_change', 'A', 'U', 'C', 'E')

exogenous_event_endpoints = {
    'investor_arrivals': 'ws://127.0.0.1:8000/hft_investor/',
    'fundamental_value_jumps': 'ws://127.0.0.1:8000/hft_jump/'
}

exogenous_event_client = 'hft_bcs/exogenous_event_client.py'

available_exchange_ports = {
    'CDA': list(range(9010, 9000, -1)),
    'FBA': list(range(9110, 9100, -1)),
    'IEX': list(range(9210, 9200, -1))
}

ouch_fields = ('price', 'time_in_force', 'display', 'buy_sell_indicator')


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