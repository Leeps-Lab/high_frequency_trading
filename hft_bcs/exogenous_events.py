from .cache import get_players_by_market, get_cache_key
from random import shuffle
from exchange import send_exchange
from .event_handlers import receive_trader_message, process_response, receive_market_message
from client_messages import broadcast
from django.core.cache import cache

def fundamental_price_change(**kwargs):
    market_id = str(kwargs.get('market'))
    all_players_data = get_players_by_market(market_id)
    responding_traders = []
    for player_data in all_players_data:
        player = player_data['model']
        trader = receive_trader_message(player.id, 
            'fundamental_price_change', **kwargs)
        responding_traders.append(trader)
    shuffle(responding_traders)
    for trader in responding_traders:
        process_response(trader)
    market = receive_market_message(market_id, 'jump', **kwargs)
    process_response(market)

def noise_trader_arrival(**kwargs):
    market_id = str(kwargs.get('market'))
    noise_trader_key = get_cache_key(market_id, 'noise_trader')
    noise_trader = cache.get(noise_trader_key)
    noise_trader.invest(**kwargs)
    process_response(noise_trader)
    cache.set(noise_trader_key, noise_trader)





        







    
