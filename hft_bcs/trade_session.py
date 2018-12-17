import subprocess
from .event_handlers import process_response, receive_market_message
from django.core.cache import cache
from .utility import exogenous_event_client, exogenous_event_endpoints
import logging
import os
from twisted.internet import reactor

log = logging.getLogger(__name__)

class TradeSessionFactory:
    @staticmethod
    def get_session(session_format):
        return LEEPSTradeSession

class TradeSession:

    events_dispatch = {
        'market_ready_to_start': 'start_trade_session',
        'market_ready_to_end': 'stop_trade_session'
    }

    def __init__(self, session):
        self.subsession = session
        self.id = str(session.code)
        self.is_trading = False
        self.markets = {}
        self.clients = {}
        self.exogenous_events = {}
        self.trading_markets = []

    def register_market(self, market_id, market_format):
        self.markets[market_id] = False
    
    def start_trade_session(self, market_id=None):
        raise NotImplementedError()
    
    def stop_trade_session(self):
        raise NotImplementedError()

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
                url = exogenous_event_endpoints[event_type]
                args = ['python', exogenous_event_client, url, filename]
                process = subprocess.Popen(args)
                self.clients[event_type] = process

    def stop_exogenous_events(self):
        for _, process in self.clients.items():
            process.kill()

        
class LEEPSTradeSession(TradeSession):

    def start_trade_session(self, market_id):
        self.markets[market_id] = True
        is_ready = (True if False not in self.markets.values() else False)
        if is_ready and not self.is_trading:
            for market_id, _ in self.markets.items():
                message_queue = receive_market_message(market_id, 'market_start')
                process_response(message_queue)
                self.trading_markets.append(market_id)
            self.run_exogenous_events()
            self.is_trading = True
            reactor.callLater(self.subsession.round_length, self.stop_trade_session)
            
    def stop_trade_session(self, *args):
        if self.is_trading:
            while self.trading_markets:
                market_id = self.trading_markets.pop()
                message_queue = receive_market_message(market_id, 'market_end')
                process_response(message_queue)
            self.stop_exogenous_events()
            self.subsession.session.advance_last_place_participants()
            self.is_trading = False
        
