
import logging
from collections import deque
from .models import Player
import itertools
from . import exchange

log = logging.getLogger(__name__)

class BaseMarket:
    market_events_dispatch = {}
    _ids = itertools.count()

    def __init__(self):
        self.id = next(self._ids)
        self.is_trading = False
        self.ready_to_trade= False
        self.exchange_address = None
        self.subscribers = {}
        self.outgoing_exchange_messages = deque()
        self.outgoing_broadcast_messages = deque()
        self.registered_session_events = []
    
    def subscribe_exchange(self, host, port, exchange_format):
        exchange.connect(self.id, host, port)
        self.exchange_address = (host, port)
    
    def reset_exchange(self):
        if self.exchange_address is None:
            raise ValueError('exchange address is not set in market %s.' % self.id)
        host , port = self.exchange_address
        exchange_message = (host, port, 'reset_exchange', 0., {'event_code': 'S'})
        self.outgoing_exchange_messages.append(exchange_message)

    def register_group(self, group_id:str, *args):
        self.subscribers[group_id] = []
        for player_id in args:
            self.subscribers[group_id].append(player_id)
    
    def receive(self, event_type, *args, **kwargs):
        if event_type not in self.market_events_dispatch:
            raise KeyError('unknown market event.')
        else:
            handler_name = self.market_events_dispatch[event_type]
            handler = getattr(self, handler_name)
            handler(*args, **kwargs)
    
    def broadcast_to_subscribers(self, broadcast_info):
        topic, data = broadcast_info
        for group_id in self.subscribers.keys():
            broadcast_message = (topic, group_id, data)
            self.outgoing_broadcast_messages.append(broadcast_message)
     
    def start_trade(self):
        if not self.ready_to_trade:
            raise ValueError('market %s not ready not trade.' % self.id)
        else:
            if self.is_trading:
                raise ValueError('market %s already trading.' % self.id)
            else:
                self.is_trading = True
                broadcast_info = ('session_start', {})
                self.broadcast_to_subscribers(broadcast_info)
    
    def end_trade(self):
        if self.is_trading:
            host, port = self.exchange_address
            exchange.disconnect(self.id, host, port)
            self.is_trading = False

    def __len__(self):
        return len(self.subscribers)

class BCSMarket(BaseMarket):
    market_events_dispatch = {
        'jump': 'fundamental_price_change',
        'player_ready': 'player_ready',
        'advance_me': 'player_reached_session_end',
        'S': 'system_event',
        'market_start': 'start_trade',
        'market_end': 'end_trade'
    }
    
    def __init__(self, **kwargs):
        super().__init__()
        for key in kwargs.keys():
            setattr(self, key, kwargs.get(key))
        self.players_in_market = {}
        self.roles = ('maker', 'sniper', 'out')
        self.role_counts = {role: 0 for role in self.roles}

    def register_group(self, group_id, players):
        super().register_group(group_id, players)
        for p in players:
            self.players_in_market[p.id] = False

    def player_ready(self, **kwargs):
        player_id = kwargs.get('player_id')
        self.players_in_market[player_id] = True
        market_ready_condition = (True if False not in self.players_in_market.values() 
            else False)
        if market_ready_condition is True:
            session_event = ('market_ready_to_start', player_id)
            self.registered_session_events.append(session_event)
    
    def player_reached_session_end(self, **kwargs):
        player_id = kwargs.get('player_id')
        self.players_in_market[player_id] = False
        session_event = ('market_ready_to_end', player_id)
        self.registered_session_events.append(session_event)

    def role_change(self, new_role:str, old_role:str, **kwargs):
        if new_role not in self.roles:
            raise KeyError('invalid role: %s' % new_role)
        self.role_counts[new_role] += 1
        self.role_counts[old_role] -= 1

    def fundamental_price_change(self, **kwargs):
        new_fp = int(kwargs['new_fundamental'])
        self.fp = new_fp
        broadcast_info = ('fundamental_price_change', {'new_price': new_fp})
        self.broadcast_to_subscribers(broadcast_info)   

           
    def system_event(self, **kwargs):
        event_code = kwargs.get('event_code')
        broadcast_info = ('batch', {'event': event_code})
        self.broadcast_to_subscribers(broadcast_info)   






