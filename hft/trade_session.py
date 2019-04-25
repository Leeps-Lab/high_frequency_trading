import subprocess
from django.core.cache import cache
from . import utility
import logging
import os
from twisted.internet import reactor
from twisted.internet import task
from .utility import format_message
from collections import deque
from . import exchange
from functools import partial
from .market import MarketFactory
from itertools import count
import sys
from django.core import serializers
from .exogenous_event import get_exogenous_event_queryset
from .internal_event_message import MarketEndMessage
from .dispatcher import ELODispatcher

log = logging.getLogger(__name__)

class TradeSessionFactory:
    @staticmethod
    def get_session(session_format):
        return ELOTradeSession

class TradeSession:

    market_factory = MarketFactory

    model_name = 'trade_session'

    events_dispatch = {
        'market_ready_to_start': 'start_trade_session',
        'market_ready_to_end': 'stop_trade_session'
    }

    def __init__(self, subsession, session_format):
        self.session_format = session_format
        self.subsession = subsession
        self.subsession_id = str(subsession.id)
        self.is_trading = False
        self.market_state = {}
        self.market_exchange_pairs = {}
        self.clients = {}
        self.exogenous_events = {}
        self.trading_markets = []
        self.outgoing_messages = deque()
        self.market_count = count(1,1)
   
    def start_trade_session(self):
        raise NotImplementedError()
    
    def stop_trade_session(self):
        raise NotImplementedError()

    def create_market(self, group_id, exchange_host, exchange_port, **kwargs):
        market_id_in_trade_session = str(next(self.market_count))
        market_cls = self.market_factory.get_market(self.session_format)
        market = market_cls(group_id, market_id_in_trade_session, self.subsession_id, 
            exchange_host, exchange_port, **kwargs)
        self.market_state[market.market_id] = False
        self.market_exchange_pairs[market.market_id] = (exchange_host, exchange_port)
        return market

    def register_exogenous_event(self, client_type, rel_path):
        self.exogenous_events[client_type] = rel_path
    
    def receive(self, event):
        self.event = event
        handler_name = self.events_dispatch[event.event_type]
        handler = getattr(self, handler_name)
        handler(event.market_id)
        self.event = None

    def start_exogenous_events(self):
        if self.exogenous_events:
            for event_type, filename in self.exogenous_events.items():
                url = utility.exogenous_event_endpoint.format(subsession_id=
                    self.subsession_id)
                exogenous_event_queryset = get_exogenous_event_queryset(event_type, 
                    filename)
                exogenous_event_json_formatted = serializers.serialize('json', 
                    exogenous_event_queryset)
                args = ['python', utility.exogenous_event_client, url, event_type, 
                    exogenous_event_json_formatted]
                process = subprocess.Popen(args)
                self.clients[event_type] = process

    @staticmethod
    def stop_exogenous_events(clients):
        for _, process in clients.items():
            process.kill()

        
class ELOTradeSession(TradeSession):
    dispatcher_cls = ELODispatcher


    def start_trade_session(self, market_id):
        def create_exchange_connection(self, market_id):
            host, port = self.market_exchange_pairs[market_id]
            exchange.connect(self.subsession_id, market_id, host, port, 
                self.dispatcher_cls, wait_for_connection=True)
        def reset_exchange(self, market_id):
            host, port = self.market_exchange_pairs[market_id]
            message_content = {'host': host, 'port': port, 'type': 'reset_exchange', 'delay':
                    0., 'order_info': {'event_code': 'S', 'timestamp': 0}}
            internal_message = format_message('exchange', **message_content)
            self.outgoing_messages.append(internal_message)
        self.market_state[market_id] = True
        is_ready = (True if False not in self.market_state.values() else False)
        if is_ready and not self.is_trading:
            for market_id, _ in self.market_state.items():
                create_exchange_connection(self, market_id)
                reset_exchange(self, market_id)
                self.event.internal_event_msgs(
                    'market_start', market_id=market_id, model=self, 
                    session_duration=self.subsession.session_duration)
                self.trading_markets.append(market_id)
            self.start_exogenous_events()
            self.is_trading = True
            deferred = task.deferLater(reactor, self.subsession.session_duration, 
                partial(self.stop_trade_session, clients=dict(self.clients)))
            
    def stop_trade_session(self, *args, clients=None):
        def stop_exchange_connection(self, market_id):
            host, port = self.market_exchange_pairs[market_id]
            exchange.disconnect(market_id, host, port)
        try:
            if self.is_trading:
                while self.trading_markets:
                    market_id = self.trading_markets.pop()
                    stop_exchange_connection(self, market_id)
                    ex_event_msg = MarketEndMessage.create(
                        'market_end', market_id=market_id, model=self)
                    self.dispatcher_cls.dispatch('internal_event', ex_event_msg)
                self.stop_exogenous_events(clients=clients)
                self.subsession.session.advance_last_place_participants()
                self.is_trading = False
        except Exception:
            log.exception('session end procedure failed')
        
