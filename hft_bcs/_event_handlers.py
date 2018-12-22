from .cache import get_cache_key, write_to_cache_with_version, cache_timeout
from . import utility
from .translator import LeepsOuchTranslator
from .subject_state import BCSSubjectState
from .trader import CDATraderFactory, FBATraderFactory
from .exchange import send_exchange
from . import client_messages 
from django.core.cache import cache
from .decorators import atomic
#TODO: this is temporarily here. there are 
# better places to keep this.

trader_factory_map = {
        'CDA': CDATraderFactory, 'FBA': FBATraderFactory
    }

SUBPROCESSES = {}

def process_response(message_queue):
    def exchange(message):
        exchange_message_type = message['type']     
        order_data = utility.pretranslate_hacks(exchange_message_type, message['order_info'])
        host, port, delay = message['host'], message['port'], message['delay']
        bytes_message = LeepsOuchTranslator.encode(exchange_message_type, **order_data)
        send_exchange(host, port, bytes_message, delay)
    def broadcast(message):
        message_type, channels_group_id = message['type'], message['group_id']
        broadcast_data = message['message']
        client_messages.broadcast(message_type, channels_group_id, **broadcast_data)
    @atomic
    def trade_session(message):
            message_type, market_id = message['type'], message['market_id']
            session_id = message['session_id']
            session_key = get_cache_key(session_id, 'trade_session')
            trade_session = cache.get(session_key)
            if trade_session.id not in SUBPROCESSES:
                SUBPROCESSES[trade_session.id] = {}
            trade_session.clients = SUBPROCESSES[trade_session.id]         
            trade_session.receive(message_type, market_id)
            SUBPROCESSES[trade_session.id] = trade_session.clients
            trade_session.clients = {}
            cache.set(session_key, trade_session, timeout=cache_timeout)
    while message_queue:
        message = message_queue.popleft()
        message_type, message_payload = message['message_type'], message['payload']
        handler = locals()[message_type]
        print('\nOUTGOING:%s\n' % message)
        handler(message_payload)

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
    message_queue = trader.outgoing_messages.copy()
    trader.outgoing_messages.clear()
    trader_data['subject_state'] = BCSSubjectState.from_trader(trader)
    version = trader_data['version'] + 1
    try:
        write_to_cache_with_version(key, trader_data, version)
    except ValueError:
        receive_trader_message(player_id, event_type, **kwargs)
    else:
        return message_queue

def receive_market_message(market_id:str, event_type:str, **kwargs):
    market_key = get_cache_key(market_id, 'market')
    market_data = cache.get(market_key)
    market, version = market_data['market'], market_data['version']
    market.receive(event_type, **kwargs)
    message_queue = market.outgoing_messages.copy()
    market.outgoing_messages.clear()
    market_data['market'] = market
    version = market_data['version'] + 1
    try:
        write_to_cache_with_version(market_key, market_data, version)
    except ValueError:
        receive_market_message(market_id, event_type, **kwargs)
    else:
        return message_queue

def receive_exchange_message(market_id, message):
    def extract_player_id(**kwargs):
        token = kwargs.get('order_token')
        if token is None:
            token = kwargs.get('replacement_order_token')
        # index 3 is subject ID      
        player_id = token[5:9]
        if token[3] == '@':
            #   way out for investor orders
            return False
        return player_id
    message_type, fields = LeepsOuchTranslator.decode(message)
    fields['type'] = message_type
    print('\nINCOMING: %s\n' % fields)
    if message_type in utility.trader_events:
        player_id = extract_player_id(**fields)
        if player_id is not False:
            message_queue = receive_trader_message(player_id, message_type, **fields)
            process_response(message_queue)
    if message_type in utility.market_events:
        market_message_queue = receive_market_message(market_id, message_type, **fields)
        process_response(market_message_queue)
    
