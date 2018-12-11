from .cache import get_cache_key, write_to_cache_with_version
from django.core.cache import cache
from .utility import client_modules
import subprocess

def spawn_subprocess(trade_session, market_id, client_type, url_to_connect, filename):
    """
    spawns a subprocess and registers it to market
    """
    code = client_modules.get(client_type)
    if code is None:
        raise KeyError('unknown client type')
    args = ('python', code, market_id, filename)
    process = subprocess.Popen(*args)
    trade_session.register_client(market_id, process, client_type)    

def map_configs_to_models(config: dict, model):
    pass

