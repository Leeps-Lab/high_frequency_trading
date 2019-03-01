import subprocess
from django.core.cache import cache
from .utility import exogenous_event_client, exogenous_event_endpoints
import logging
import os
from twisted.internet import reactor
from twisted.internet import task
from .utility import format_message
from .cache import get_cache_key
from collections import deque
from . import exchange
from .dispatcher import LEEPSDispatcher
from functools import partial
from .market import MarketFactory
from itertools import count
from .dispatcher import LEEPSDispatcher
from otree.timeout.tasks import hft_background_task
import sys

log = logging.getLogger(__name__)

class TradeSessionFactory:
    @staticmethod
    def get_session(session_format):
        return LEEPSTradeSession

class TradeSession:

    market_factory = MarketFactory

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
   
    def start_trade_session(self, market_id=None):
        raise NotImplementedError()
    
    def stop_trade_session(self):
        raise NotImplementedError()

    def create_market(self, exchange_host, exchange_port):
        market_id_in_trade_session = str(next(self.market_count))
        market_cls = self.market_factory.get_market(self.session_format)
        market = market_cls(market_id_in_trade_session, self.subsession_id, 
            exchange_host, exchange_port)
        self.market_state[market.market_id] = False
        self.market_exchange_pairs[market.market_id] = (exchange_host, exchange_port)
        return market

    def register_exogenous_event(self, client_type, filename):
        path = os.path.join(os.getcwd(), filename)
        self.exogenous_events[client_type] = path
    
    def receive(self, event_type, market_id):
        handler_name = self.events_dispatch[event_type]
        handler = getattr(self, handler_name)
        handler(market_id)

    def run_exogenous_events(self):
        if self.exogenous_events:
            for event_type, filename in self.exogenous_events.items():
                url = exogenous_event_endpoints[event_type].format(subsession_id=
                    self.subsession_id)
                args = ['python', exogenous_event_client, event_type, url, filename]
                process = subprocess.Popen(args)
                self.clients[event_type] = process

    @staticmethod
    def stop_exogenous_events(clients):
        for _, process in clients.items():
            process.kill()

        
class LEEPSTradeSession(TradeSession):

    def start_trade_session(self, market_id):
        def create_exchange_connection(self, market_id):
            host, port = self.market_exchange_pairs[market_id]
            exchange.connect(self.subsession_id, market_id, host, port, 
                LEEPSDispatcher, wait_for_connection=True)
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
                message_content = {'type': 'market_start', 'market_id': market_id,
                    'subsession_id': self.subsession_id}
                message = format_message('derived_event', **message_content)
                self.outgoing_messages.append(message)
                self.trading_markets.append(market_id)
            self.run_exogenous_events()
            self.is_trading = True
            deferred = task.deferLater(reactor, self.subsession.round_length, 
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
                    message_content = {'type': 'market_end', 'market_id': market_id,
                        'subsession_id': self.subsession_id}
                    message = format_message('derived_event', **message_content)
                    LEEPSDispatcher.dispatch(message['message_type'], message)
                self.stop_exogenous_events(clients=clients)
                self.subsession.session.advance_last_place_participants()
                self.is_trading = False
        except:
            log.exception('session end procedure failed')
        
