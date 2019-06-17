from django.core.cache import cache
import logging

log = logging.getLogger(__name__)


model_key_format_str_attr = '{model.model_name}_{model.model_id}_{model.subsession_id}'
model_key_format_str_kw = '{model_name}_{model_id}_{subsession_id}'

def get_cache_key(type_code, model=None, model_name=None, model_id=None, 
    subsession_id=None):
    if type_code is 'from_model':
        if model is None:
            raise ValueError('model not set.')
        else:
            return model_key_format_str_attr.format(model=model)
    elif type_code is 'from_kws':
        req_kws = (model_name, model_id, subsession_id)
        null_kws = [x for x in req_kws if x is None]
        if null_kws:
            raise ValueError(','.join(n for n in null_kws) + 'can\'t be none.')
        else:
            return model_key_format_str_kw.format(model_name=model_name,
                model_id=model_id, subsession_id=subsession_id)

lock_key_format_str = '{cache_key}_lock'
cache_timeout = 30 * 60


def initialize_model_cache(model, timeout=cache_timeout, **kwargs):
    model_cache_key = get_cache_key('from_kws', **get_model_ids(model))
    cache.set(model_cache_key, model, timeout=cache_timeout)
    log.debug('set cache key %s' % model_cache_key)


def get_trader_ids_by_market(market_id: str, subsession_id: str):
    market_key = get_cache_key('from_kws', model_name='market', 
        model_id=market_id, subsession_id=subsession_id)
    market = cache.get(market_key)
    trader_ids = list(market.players_in_market.keys())
    return trader_ids

market_id_mapping_key = 'MARKET_ID_MAP_{subsession_id}'


def set_market_id_table(subsession_id, mapping: dict, timeout=cache_timeout):
    key = market_id_mapping_key.format(subsession_id=subsession_id)
    cache.set(key, mapping, timeout=timeout)


def get_market_id_table(subsession_id):
    key = market_id_mapping_key.format(subsession_id=subsession_id)
    return cache.get(key)


id_fields = {
    'inv': 'market_id', 'market': 'market_id', 'trade_session': 'subsession_id',
    'trader': 'player_id'}

def get_model_ids(model):
    model_name = model.model_name
    model_id = getattr(model, id_fields[model_name])
    subsession_id = model.subsession_id
    return {'model_name': model_name, 'model_id': model_id, 
        'subsession_id': subsession_id}
