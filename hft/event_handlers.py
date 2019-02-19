from .cache import (get_cache_key, write_to_cache_with_version, cache_timeout,
    get_trader_ids_by_market)
from . import utility
from .subject_state import SubjectStateFactory
from .trader import CDATraderFactory, FBATraderFactory, ELOTraderFactory 
from django.core.cache import cache
from .decorators import atomic
from random import shuffle
from otree.timeout.tasks import hft_background_task
from . import checkpoints

import logging
log = logging.getLogger(__name__)

trader_factory_map = {
    'BCS': {'CDA': CDATraderFactory, 'FBA': FBATraderFactory},
    'elo': {'CDA': ELOTraderFactory}
    }

SUBPROCESSES = {}

class HandlerFactory:

    @staticmethod
    def get_handler(handler_type):
        if handler_type == 'trader':
            return leeps_handle_trader_message
        elif handler_type == 'market':
            return leeps_handle_market_message
        elif handler_type == 'trade_session':
            return leeps_handle_session_events
        elif handler_type == 'noise_trader_arrival':
            return leeps_handle_investor_event
        elif handler_type == 'marketwide_events':
            return marketwide_events
        elif handler_type == 'role_based_events':
            return role_based_events
        else:
            raise Exception('unknown event: %s' % handler_type)

def leeps_handle_trader_message(event, exchange_format='CDA', session_format='elo', 
        **kwargs):
    player_id = event.player_id
    # player_id = event.attachments.get('player_id')
    # if player_id is None:
    #     player_id = event.message.get('player_id')   
    if player_id is None:
        raise Exception('player id is missing in event %s.' % event)
    if player_id == 0:
        return _handle_investors(event)
        # event.attachments['note'] = 'investor'
        # hft_background_task(checkpoints.hft_investor_checkpoint, event)
    key = get_cache_key(player_id ,'trader')
    trader_data = cache.get(key)
    if trader_data is None:
        raise ValueError('trader key: %s returned none.' % key)
    if event.event_type == 'role_change':
        trader_data['role'] = event.message.state
    role_name, subject_state = trader_data['role'], trader_data['subject_state']
    TraderFactory = trader_factory_map[session_format][exchange_format]
    trader = TraderFactory.get_trader(role_name, subject_state)
    trader.receive(event)
    message_queue = trader.outgoing_messages.copy()
    trader.outgoing_messages.clear()
    event.outgoing_messages.extend(message_queue)
    state_cls = SubjectStateFactory.get_state(session_format)
    trader_state = state_cls.from_trader(trader)
    trader_data['subject_state'] = trader_state
    version = trader_data['version'] + 1
    try:
        write_to_cache_with_version(key, trader_data, version)
    except ValueError:
        log.warning('version mismatch in key: %s, recalculating..' % key)
        leeps_handle_trader_message(event, **kwargs)
    else:
        hft_background_task(checkpoints.hft_trader_checkpoint, player_id, 
            trader_state, event.to_kwargs())  
        return event

def leeps_handle_market_message(event, **kwargs):
    # fields = utility.kwargs_from_event(event)
    if event.event_type == 'A' and event.player_id!= 0:
        return event
    market_key = get_cache_key(event.market_id, 'market')
    market_data = cache.get(market_key)
    if market_data is None:
        raise Exception('market key: %s returned none, event: %s' % (market_key,
            event))
    market, version = market_data['market'], market_data['version']  
    attachments = market.receive(event)
    if attachments:
        event.attachments.update(attachments)
    message_queue = market.outgoing_messages.copy()
    if event.event_type in market.attachments_for_observers:
        event.attachments.update(market.attachments_for_observers[event.event_type])
    market.outgoing_messages.clear()
    event.outgoing_messages.extend(message_queue)
    market_data['market'] = market
    version = market_data['version'] + 1
    try:
        write_to_cache_with_version(market_key, market_data, version)
    except ValueError:
        leeps_handle_market_message(event, **kwargs)
    else:
        return event

def _handle_investors(event):
    key = get_cache_key(event.player_id, 'investor', market_id=event.market_id)
    investor_data = cache.get(key)
    investor, version = investor_data['investor'], investor_data['version']
    if investor is None:
        raise ValueError('investor key: %s returned none.' % key)
    investor.receive(event)
    message_queue = investor.outgoing_messages.copy()
    investor.outgoing_messages.clear()
    event.outgoing_messages.extend(message_queue)
    investor_data['investor'] = investor
    new_version = version + 1
    try:
        write_to_cache_with_version(key, investor_data, new_version)
    except ValueError:
        log.warning('version mismatch in key: %s, recalculating..' % key)
        _handle_investors(event)
    return event

@atomic
def leeps_handle_session_events(event, **kwargs):
    session_key = get_cache_key(event.subsession_id, 'trade_session')
    trade_session = cache.get(session_key)
    subsession_id = trade_session.subsession_id
    if subsession_id not in SUBPROCESSES:
        SUBPROCESSES[subsession_id] = {}
    trade_session.clients = SUBPROCESSES[subsession_id]      
    trade_session.receive(event.event_type, event.market_id)
    SUBPROCESSES[subsession_id] = trade_session.clients
    trade_session.clients = {}
    message_queue = trade_session.outgoing_messages.copy()
    trade_session.outgoing_messages.clear()
    event.outgoing_messages.extend(message_queue)    
    cache.set(session_key, trade_session, timeout=cache_timeout)
    return event

def marketwide_events(event, **kwargs):
    traders_in_market = get_trader_ids_by_market(event.market_id)
    for trader_id in traders_in_market:
        event.player_id = trader_id
        event = leeps_handle_trader_message(event, **kwargs)
    shuffle(event.outgoing_messages)
    return event

def role_based_events(event, **kwargs):
    makers = event.message.maker_ids
    if makers:
        for trader_id in makers:
            event.player_id = trader_id
            event = leeps_handle_trader_message(event, **kwargs)
        shuffle(event.outgoing_messages)
    return event