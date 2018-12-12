
from django.core.cache import cache

cache_key_format = {
    'player': 'PLAYER_DATA_{model_id}',
    'trader': 'TRADER_DATA_{model_id}',
    'market': 'MARKET_DATA_{model_id}',
    'trade_session': 'SESSION_DATA_{model_id}',
    'noise_trader': 'NOISE_TRADER_{model_id}'
}

cache_timeout = 30 * 60 

def get_cache_key(model_id, key_model_name):
    try:
        key = cache_key_format[key_model_name].format(model_id)   
    except KeyError:
        raise ValueError('invalid model: %s' % key_model_name)
    return key

def write_to_cache_with_version(key, value, version, timeout=cache_timeout):
    current_version_no = cache.get(key)['version']
    if not (version - current_version_no == 1):
        raise ValueError('version mismatch: %s x %s in %s' % (current_version_no, version, key))
    value['version'] = version
    cache.set(key, value, timeout=timeout)

def initialize_player_cache(player, state_cls, ordersore_cls, fields_to_map, timeout=cache_timeout):
    pairs = {}
    player_key = get_cache_key(player.id, 'player')
    pairs[player_key] = {'model': player}
    subject_state_data = {k: getattr(player, k, None) for k in fields_to_map}
    subject_state_data.update({'orderstore': ordersore_cls(player.id_in_group)})
    trader_key = get_cache_key(player.id, 'trader')
    pairs[trader_key] = {'version': 0, 'role': player.role, 
        'subject_state': state_cls(**subject_state_data)}
    for k, v in pairs.items():
        cache.set(k, v, timeout=timeout) 

def initialize_market_cache(market, timeout=cache_timeout, **kwargs):
    market_data = {'version': 0, 'market': market}
    market_key = get_cache_key(market.id, 'market')
    cache.set(market_key, market_data, timeout=timeout)

def initialize_session_cache(session, timeout=cache_timeout, **kwargs):
    session_key = get_cache_key('active_session', 'trade_session')
    cache.set(session_key, session, timeout=timeout)

def get_players_by_market(market_id:str):
    market_key = get_cache_key(market_id, 'market')
    market = cache.get(market_key)
    players_data = [] 
    for _, player_ids in market.subscribers.items():
        for pid in player_ids:
            player_key = get_cache_key(pid, 'player')
            player = cache.get(player_key)
            players_data.append(player)
    return players_data
