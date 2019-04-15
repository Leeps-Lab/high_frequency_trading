

model_key_format_str_attr = '{model.model_name}_{model.model_id}_{model.subsession_id}'
model_key_format_str_kw = '{model_name}_{model_id}_{subsession_id}'
lock_key_format_str = '{cache_key}_lock'
cache_timeout = 30 * 60


def initialize_model_cache(model, timeout=cache_timeout, **kwargs):
    model_cache_key = model_key_format_str_attr.format(model=model, model_name)
    cache.set(model_cache_key, model, timeout=cache_timeout)


def get_trader_ids_by_market(market_id: str, subsession_id: str):
    market_key = model_key_format_str_kw.format(
        model_name='market', model_id=market_id, subsession_id=subsession_id)
    market_data = cache.get(market_key)
    trader_ids = []
    for group_id, players_list in market_data['market'].subscribers.items():
        trader_ids.extend(players_list)
    return trader_ids

market_id_mapping_key = 'MARKET_ID_MAP_{subsession_id}'


def set_market_id_map(subsession_id, mapping: dict, timeout=cache_timeout):
    key = market_id_mapping_key.format(subsession_id=subsession_id)
    cache.set(key, mapping, timeout=timeout)


def get_market_id_map(subsession_id):
    key = market_id_mapping_key.format(subsession_id=subsession_id)
    return cache.get(key)
