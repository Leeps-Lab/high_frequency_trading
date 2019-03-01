from django.core.cache import cache

cache_key_format = {
    'player': 'PLAYER_{model_id}',
    'trader': 'TRADER_{model_id}',
    'market': 'MARKET_{model_id}',
    'investor': 'INVESTOR_{subsession_id}_{model_id}_{market_id}',
    'trade_session': 'SESSION_{model_id}',
}

cache_timeout = 30 * 60 

def get_cache_key(model_id, key_model_name, **kwargs):
    try:
        key_format = cache_key_format[key_model_name] 
    except KeyError:
        raise ValueError('invalid model: %s' % key_model_name)
    key = key_format.format(model_id=model_id, **kwargs) 
    return key

def write_to_cache_with_version(key, value, version, timeout=cache_timeout):
    current_version_no = cache.get(key)['version']
    if not (version - current_version_no == 1):
        raise ValueError('version mismatch: %s x %s in %s' % (current_version_no, version, key))
    value['version'] = version
    cache.set(key, value, timeout=timeout)

def initialize_player_cache(player, trader_state, timeout=cache_timeout):
    trader_key = get_cache_key(player.id, 'trader')
    trader_data = {'version': 0, 'role': player.role, 
        'subject_state': trader_state}
    cache.set(trader_key, trader_data)

def initialize_market_cache(market, timeout=cache_timeout, **kwargs):
    market_data = {'version': 0, 'market': market}
    market_key = get_cache_key(market.market_id, 'market')
    cache.set(market_key, market_data, timeout=timeout)
    return market_data

def initialize_session_cache(session, timeout=cache_timeout, **kwargs):
    session_key = get_cache_key(session.subsession_id, 'trade_session')
    cache.set(session_key, session, timeout=timeout)

def initialize_investor_cache(investor, timeout=cache_timeout, **kwargs):
    investor_key = get_cache_key(investor.id, 'investor', market_id=investor.market_id,
        subsession_id=investor.subsession_id)
    investor_data = {'version': 0, 'investor': investor}
    cache.set(investor_key, investor_data, timeout=timeout)
    cache.ttl(investor_key)

def get_trader_ids_by_market(market_id:str):
    market_key = get_cache_key(market_id, 'market')
    market_data = cache.get(market_key)
    trader_ids = []
    for group_id, players_list in market_data['market'].subscribers.items():
        trader_ids.extend(players_list)
    return trader_ids


market_id_mapping_key = 'MARKET_ID_MAP_{subsession_id}'
def set_market_id_map(subsession_id, mapping:dict, timeout=cache_timeout):
    key = market_id_mapping_key.format(subsession_id=subsession_id)
    cache.set(key, mapping, timeout=timeout)

def get_market_id_map(subsession_id):
    key = market_id_mapping_key.format(subsession_id=subsession_id)
    return cache.get(key)