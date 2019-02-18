import time
import datetime
import pytz
import logging
from . import market_environments
from otree.api import ( 
    models, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
)

SESSION_FORMAT = None
EXCHANGES = None

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

exogenous_event_client = 'hft/exogenous_event_client.py'

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

def type_check_configs(session_format, session_configs):
    market_settings = market_environments.environments[session_format]
    cleaned_configs = dict(session_configs)
    for k, v in session_configs.items():
        try:
            field_cls = market_settings.config_field_type[k]
        except KeyError:
            continue
        else:
            try:
                cleaned_configs[k] = field_cls(v)
            except:
                log.error('type check/cast failed for config key: %s and value: %s for type: %s.' 
                    % (k, v, field_cls))
                raise 
    return cleaned_configs

def scale_configs(session_format, session_configs):
    market_settings = market_environments.environments[session_format]
    scaled_configs = dict(session_configs)  
    for k, v in session_configs.items():
        try:
            scale = market_settings.fields_to_scale[k]
        except KeyError:
            continue
        else:
            try:
                scaled_configs[k] = v * int(scale)
            except:
                log.error('scaling failed for config key: %s and value: %s for scale: %s.' 
                    % (k, v, scale))
                raise 
    return scaled_configs


        
def configure_model_for_market(model_name, model, session_format:dict, session_configs:dict):
    market_settings = market_environments.environments[session_format]
    mapping = market_settings.model_configuration[model_name]
    for k, v in mapping.items():
        field_value = session_configs[k]
        try:
            setattr(model, v, field_value)
        except:
            log.error('failed to set field: %s on model: %s with value: %s.' %
                (k, v, field_value))
            raise
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


def kwargs_from_event(event):
    kwargs = event.message.copy()
    for k, v in event.attachments.items():
        if k not in kwargs and v is not None:
            kwargs[k] = v
    return kwargs




