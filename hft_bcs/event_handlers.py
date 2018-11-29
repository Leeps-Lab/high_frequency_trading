from .cache import get_cache_key, write_to_cache_with_version
from .utility import pretranslate_hacks
from .new_translator import BCSTranslator
from .subject_state import BCSSubjectState
from .trader import CDATraderFactory, FBATraderFactory
from .exchange import send_exchange
from . import client_messages 
from django.core.cache import cache


trader_factory_map = {
        'CDA': CDATraderFactory, 'FBA': FBATraderFactory
    }

def process_trader_response(exchange_messages, broadcast_messages):
    def process_exchange_response(exchange_messages):
        for message_data in exchange_messages:
            host, port, message_type, delay, order_data = message_data
            order_data = pretranslate_hacks(message_type, order_data)
            bytes_message = BCSTranslator.encode(message_type, **order_data)
            send_exchange(host, port, bytes_message, delay)
    def process_broadcast_response(broadcast_messages):
        for message_data in broadcast_messages:
            message_type, message_group_id, broadcast_data = message_data
            client_messages.broadcast(message_type, message_group_id, **broadcast_data)
    if exchange_messages is not None:
        process_exchange_response(exchange_messages)
    if broadcast_messages is not None:
        process_broadcast_response(broadcast_messages)

def receive_trader_message(session_format: str, player_id: str, event_type: str, **kwargs):
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
        receive_trader_message(session_format, player_id, event_type, **kwargs)
    else:
        return trader
