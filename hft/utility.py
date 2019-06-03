import time
import datetime
import pytz
import logging
from . import market_environments
from collections import namedtuple

SESSION_FORMAT = None
EXCHANGES = None

log = logging.getLogger(__name__)

DEFAULT_TIMEZONE = pytz.timezone('US/Pacific')

exogenous_events = {
    'BCS': ['investor_arrivals', 'fundamental_value_jumps'],
    'LEEPS': ['investor_arrivals']
}  

exogenous_event_endpoint = 'ws://127.0.0.1:8000/hft_exogenous_event/{subsession_id}'
exogenous_event_client = 'hft/exogenous_event_emitter.py'

available_exchange_ports = {
    'CDA': list(range(9010, 9000, -1)),
    'FBA': list(range(9110, 9100, -1)),
    'IEX': list(range(9210, 9200, -1))
}

MAX_ASK = 2147483647
MIN_BID = 0


# class dotdict(dict):
#     """dot.notation access to dictionary attributes"""
#     __getattr__ = dict.get
#     __setattr__ = dict.__setitem__
#     __delattr__ = dict.__delitem__


# def format_message(message_type, **kwargs):
#     message = {'message_type': message_type, 'payload': {} }
#     for k, v in kwargs.items():
#         message['payload'][k] = v
#     return message

def process_configs(session_format, session_configs):
    clean_confs = type_check_configs(
        session_format, session_configs)
    clean_confs = scale_configs(
        session_format, clean_confs)
    return clean_confs

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
                log.exception('type check/cast failed for config key: %s and value: %s for type: %s.' 
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
                scaled_configs[k] = int(v * int(scale))
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

        
def ensure_results_ready(subsession_id, market_id, record_cls, num_players,
                         timeout=90, sleep_time=1):
    total_slept = 0
    results_ready = False
    while total_slept < timeout:
        num_results_ready = record_cls.objects.filter(subsession_id=
            subsession_id, market_id=market_id, trigger_event_type=
            'market_end').count()
        log.warning('waiting results for market {}, {}/{} results ready'.format(
            market_id, num_results_ready, num_players))            
        if  num_results_ready == num_players:
            results_ready = True
            break
        else:
            time.sleep(sleep_time)
            total_slept += sleep_time
    return results_ready


elo_args_fields = (
    'subsession_id', 'market_id', 'id', 'id_in_group', 'default_role', 
    'exchange_host', 'exchange_port')
elo_kwargs_fields = ('cash', )
def elo_otree_player_converter(otree_player):
    args = [getattr(otree_player, field) for field in elo_args_fields]
    kwargs = {field: getattr(otree_player, field) for field in elo_kwargs_fields}
    return args, kwargs


def validate_bbo(bb, bo):
    if bb == MIN_BID or bo == MAX_ASK:
        return False
    else: return True

def market_is_valid(market_facts):
    focal_bbo_is_valid = validate_bbo(market_facts['best_bid'], market_facts['best_offer'])
    external_bbo_is_valid = validate_bbo(market_facts['e_best_bid'], market_facts['e_best_offer'])
    return focal_bbo_is_valid and external_bbo_is_valid
