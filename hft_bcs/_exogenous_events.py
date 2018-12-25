from .cache import get_players_by_market, get_cache_key
from random import shuffle
from .exchange import send_exchange
from .event_handlers import receive_trader_message, process_response, receive_market_message
from .client_messages import broadcast
from django.core.cache import cache
from .trader import LEEPSInvestor
from .subject_state import LEEPSInvestorState

def fundamental_price_change(**kwargs):
    market_id = str(kwargs.pop('market_id'))
    all_players_data = get_players_by_market(market_id)
    responding_traders = []
    for player_data in all_players_data:
        player = player_data['model']
        trader_message_queue = receive_trader_message(player.id, 
            'fundamental_price_change', **kwargs)
        responding_traders.append(trader_message_queue)
    shuffle(responding_traders)
    for message_queue in responding_traders:
        process_response(message_queue)
    market_message_queue = receive_market_message(market_id, 'jump', **kwargs)
    process_response(market_message_queue)

integer_fields = ('price', 'time_in_force')
def noise_trader_arrival(**kwargs):
    market_id = str(kwargs.pop('market_id'))
    kwargs['price'] = int(kwargs['price'] )
    kwargs['time_in_force'] = int(kwargs['time_in_force'])
    message_queue = receive_market_message(market_id, 'noise_trader_arrival', **kwargs)
    process_response(message_queue)




    


        







    
