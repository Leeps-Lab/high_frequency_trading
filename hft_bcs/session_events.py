from .cache import get_cache_key, write_to_cache_with_version
from django.core.cache import cache

def player_ready(group_id, player_id):
    key = get_cache_key(group_id, 'group')
    group_data = cache.get(key)
    group_data['players'][player_id] = True
    version = group_data['version']
    write_to_cache_with_version(key, group_data, version + 1)
    

