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

def clean_configs(session_format, session_configs):
    market_settings = market_environments.environments[session_format]
    clean_configs = dict(session_configs)
    for k, v in session_configs.items():
        try:
            field_cls, scale = market_settings.config_field_type_and_scale[k]
        except KeyError:
            continue
        clean_configs[k] = field_cls(v) * int(scale)
    return clean_configs
        
def configure_model(model, session_format:dict, session_configs:dict):
    def validate_model(model):
        if isinstance(model, BasePlayer):
            return 'player'
        elif isinstance(model, BaseSubsession):
            return 'subsession'
        else:
            raise ValueError('invalid model %s' % model.__class__.__name__)
    model_type = validate_model(model)
    market_settings = market_environments.environments[session_format]
    mapping = market_settings.model_configuration[model_type]
    for k, v in mapping.items():
        field_value = session_configs[k]
        print(model, v, field_value)
        setattr(model, v, field_value)
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




