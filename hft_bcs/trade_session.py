import subprocess
from .cache import get_cache_key, write_to_cache_with_version
from event_handlers import process_response, receive_market_message
from django.core.cache import cache
from .utility import exogenous_event_client, exogenous_event_endpoints
import logging

log = logging.getLogger(__name__)

class TradeSession:

    events_dispatch = {
        'market_ready_to_start': 'end_trade',
        'market_ready_to_end': 'start_trade'
    }

    def __init__(self, session):
        self.session = session
        self.id = str(session.code)
        self.markets = {}
        self.clients = {}
        self.exogenous_events = {}
        self.trading_markets = []

    def register_market(self, market_id, market_format):
        self.markets[market_id] = market_format
        self.clients[market_id] = {}
        self.exogenous_events[market_id] = {}
    
    def start_trade_session(self, market_id=None):
        raise NotImplementedError
    
    def stop_trade_session(self):
        raise NotImplementedError

    def register_exogenous_event(self, market_id, client_type, filename):
        self.exogenous_events[market_id][client_type] = filename 
    
    def run_exogenous_events(self, market_id):
        exogenous_events = self.exogenous_events[market_id]
        if exogenous_events:
            for event_type, filename in exogenous_events.items():
                url = exogenous_event_endpoints[event_type]
                args = ('python', exogenous_event_client, market_id, url, filename)
                process = subprocess.Popen(*args)
                self.clients[market_id][event_type] = process

    def stop_exogenous_events(self, market_id):
        exogenous_events = self.clients[market_id]
        for _, process in exogenous_events.items:
            process.kill()

        
class LEEPSTradeSession(TradeSession):

    def start_trade_session(self):
        for market_id, _ in self.markets:
            market = receive_market_message(market_id, 'market_start')
            self.run_exogenous_events(market_id)
            process_response(market)
            self.trading_markets.append(market_id)
        
    def stop_trade_session(self):
        for market_id, _ in self.markets:
            market = receive_market_message(market_id, 'market_end')
            self.stop_exogenous_events(market_id)
            process_response(market)
            self.trading_markets.pop(market_id)
        self.session.advance_last_place_participants()
