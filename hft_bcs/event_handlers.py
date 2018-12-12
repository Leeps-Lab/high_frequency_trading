from .cache import get_cache_key, write_to_cache_with_version
from .utility import pretranslate_hacks
from .translator import LeepsOuchTranslator
from .subject_state import BCSSubjectState
from .trader import CDATraderFactory, FBATraderFactory
from .exchange import send_exchange
from . import client_messages 
from django.core.cache import cache
from .models import Constants
from .decorators import atomic
#TODO: this is temporarily here. there are 
# better places to keep this.

trader_factory_map = {
        'CDA': CDATraderFactory, 'FBA': FBATraderFactory
    }

def process_response(data_model):
    def outgoing_exchange_messages(exchange_messages):
        while exchange_messages:
            host, port, message_type, delay, order_data = exchange_messages.popleft()
            order_data = pretranslate_hacks(message_type, order_data)
            bytes_message = LeepsOuchTranslator.encode(message_type, **order_data)
            send_exchange(host, port, bytes_message, delay)
    def outgoing_broadcast_messages(broadcast_messages):
        while broadcast_messages:
            message_type, message_group_id, broadcast_data = broadcast_messages.popleft()
            client_messages.broadcast(message_type, message_group_id, **broadcast_data)
    @atomic
    def registered_session_events(session_events):
        while session_events:
            session_key = get_cache_key('active_session', 'trade_session')
            trade_session = cache.get(session_key)
            trade_session.receive()
    for message_bus_name in ('outgoing_exchange_messages', 'outgoing_broadcast_messages', 
        'registered_session_events'):
        messages = getattr(data_model, message_bus_name)
        handler = locals()[message_bus_name]
        handler(messages)

def receive_trader_message(player_id: str, event_type: str, session_format='CDA', **kwargs):
    key = get_cache_key(player_id ,'trader')
    trader_data = cache.get(key)
    if event_type == 'role_change':
        # temporary for testing.
        trader_data['role'] = kwargs['state'].lower()
    role_name, subject_state = trader_data['role'], trader_data['subject_state']
    TraderFactory = trader_factory_map[session_format]
    trader = TraderFactory.get_trader(role_name, subject_state)
    trader.receive(**kwargs)
    trader_data['subject_state'] = BCSSubjectState.from_trader(trader)
    version = trader_data['version'] + 1
    try:
        write_to_cache_with_version(key, trader_data, version)
    except ValueError:
        receive_trader_message(player_id, event_type, **kwargs)
    else:
        return trader

def receive_market_message(market_id:str, event_type:str, **kwargs):
    market_key = get_cache_key(market_id, 'market')
    market_data = cache.get(market_key)
    market, version = market_data['market'], market_data['version']
    market.receive(event_type, **kwargs)
    market_data['market'] = market
    version = market_data['version'] + 1
    try:
        write_to_cache_with_version(market_key, market_data, version)
    except ValueError:
        receive_market_message(market_id, event_type, **kwargs)
    else:
        return market

def receive_exchange_message(market_id, message):
    def extract_player_id(**kwargs):
        token = fields.get('order_token')
        if token is None:
            token = fields.get('replacement_order_token')
        # index 3 is subject ID      
        player_id = ord(token[3]) - 64
        return player_id
    message_type, fields = LeepsOuchTranslator.decode(message)
    if message_type in Constants.market_events:
        receive_market_message(market_id, message_type, **fields)
    



