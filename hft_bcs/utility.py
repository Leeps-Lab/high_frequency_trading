import time
import numpy as np
import datetime
import pytz
import logging
import os 
import yaml
log = logging.getLogger(__name__)

DEFAULT_TIMEZONE = pytz.timezone('US/Pacific')

exogenous_event_endpoints = {
    'investor': 'ws://127.0.0.1:8000/hft_investor/',
    'jump': 'ws://127.0.0.1:8000/hft_jump/'
}

exogenous_event_client = 'hft_bcs/exogenous_event.py'

available_exchange_ports = {
    'CDA': list(range(9010, 9000, -1)),
    'FBA': list(range(9110, 9100, -1)),
    'IEX': list(range(9210, 9200, -1))
}

ouch_fields = ('price', 'time_in_force', 'display', 'buy_sell_indicator')


def scale_configs(scaling_map, session_configs):
    adjusted_configs = dict(session_configs)
    for k, v in session_configs.items():
        try:
            adjusted_configs[k] = v * scaling_map[k]
        except KeyError:
            log.info('missing key %s:%s, skip..', k, v)
        
def from_configs_to_models(configs:dict, mapping:dict, **models):
    """
    map configs to database models
    """
    for model_name, field_map in mapping.items():
        for k, v in field_map.items():
            config_value = configs[k]
            for model in models[model_name]:
                setattr(model, v, config_value)
                model.save()

def read_yaml_config(filename, path='session_config/session_configs') -> dict:
    path = os.path.join(os.getcwd(), filename)
    with open(path, 'r') as f:
        try:
            config = yaml.load(f)
        except yaml.YAMLError as e:
            raise e
        else:
            log.debug('read custom config: %s.' % path)
    return config

def pretranslate_hacks(message_type, message_data):
    if message_type == 'replace':
        message_data['price'] = message_data['replace_price']
    return message_data
