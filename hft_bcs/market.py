
import logging
from collections import deque
import itertools
from . import exchange
from .event_handlers import receive_exchange_message
from .trader import LEEPSInvestor
from .subject_state import LEEPSInvestorState
from .orderstore import OrderStore
from .utility import format_message

from .equations import order_imbalance_function
log = logging.getLogger(__name__)

class MarketFactory:
    @staticmethod
    def get_market(session_format):
        return BCSMarket

class BaseMarket:
    market_events_dispatch = {}
    _ids = itertools.count()

    def __init__(self):
        self.id = next(self._ids)
        self.is_trading = False
        self.ready_to_trade= False
        self.exchange_address = None
        self.subscriber_groups = {}
        self.players_in_market = {}
        self.outgoing_messages = deque()
    
    def create_exchange_connection(self):
        host, port = self.exchange_address
        exchange.connect(self.id, host, port, receive_exchange_message, wait_for_connection=True)

    def add_exchange(self, host, port):
        self.exchange_address = (host, port)
    
    def register_session(self, trade_session_id):
        self.session_id = trade_session_id
    
    def reset_exchange(self):
        if self.exchange_address is None:
            raise ValueError('exchange address is not set in market %s.' % self.id)
        host, port = self.exchange_address
        message_content = {'host': host, 'port': port, 'type': 'reset_exchange', 'delay':
                0., 'order_info': {'event_code': 'S', 'timestamp': 0}}
        internal_message = format_message('exchange', **message_content)
        self.outgoing_messages.append(internal_message)

    def register_group(self, group):
        self.subscriber_groups[group.id] = []
        for player in group.get_players():
            self.subscriber_groups[group.id].append(player.id)
    
    def receive(self, event_type, *args, **kwargs):
        if event_type not in self.market_events_dispatch:
            raise KeyError('unknown market event.')
        else:
            handler_name = self.market_events_dispatch[event_type]
            handler = getattr(self, handler_name)
            handler(*args, **kwargs)
    
    def broadcast_to_subscribers(self, broadcast_info):
        topic, data = broadcast_info
        for group_id in self.subscriber_groups.keys():
            message_content = { 'group_id': group_id, 'type': topic, 
            'message': data}
            internal_message = format_message('broadcast', **message_content)            
            self.outgoing_messages.append(internal_message)
     
    def start_trade(self):
        if not self.ready_to_trade:
            raise ValueError('market %s not ready not trade.' % self.id)
        else:
            if self.is_trading:
                raise ValueError('market %s already trading.' % self.id)
            else:
                self.is_trading = True
                self.create_exchange_connection()
                self.reset_exchange()
                broadcast_info = ('session_start', {})
                self.broadcast_to_subscribers(broadcast_info)
    
    def end_trade(self):
        if self.is_trading:
            host, port = self.exchange_address
            exchange.disconnect(self.id, host, port)
            self.is_trading = False

    def __len__(self):
        return len(self.subscriber_groups)

class BCSMarket(BaseMarket):
    market_events_dispatch = {
        'jump': 'fundamental_price_change',
        'noise_trader_arrival': 'noise_trader_arrival',
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
        self.roles = ('maker', 'sniper', 'out')
        self.role_counts = {role: 0 for role in self.roles}
        self.investor = None

    def register_group(self, group):
        super().register_group(group)
        for p in group.get_players():
            self.players_in_market[p.id] = False
            p.market = self.id
            p.save()

    def player_ready(self, **kwargs):
        player_id = kwargs.get('player_id')
        self.players_in_market[player_id] = True
        market_ready_condition = (True if False not in self.players_in_market.values() 
            else False)
        if market_ready_condition is True:
            self.ready_to_trade = True
            message_content = {'type': 'market_ready_to_start', 'market_id': self.id,
                'session_id': self.session_id}
            internal_message = format_message('trade_session', **message_content)
            self.outgoing_messages.append(internal_message)
    
    def player_reached_session_end(self, **kwargs):
        player_id = kwargs.get('player_id')
        self.players_in_market[player_id] = False
        message_content = {'type': 'market_ready_to_end', 'market_id': self.id,
                'session_id': self.session_id}
        internal_message = format_message('trade_session', **message_content)
        self.outgoing_messages.append(internal_message)

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
    
    def noise_trader_arrival(self, **kwargs):
        host, port = self.exchange_address
        if self.investor is None:
            fields = {'exchange_host': host, 'exchange_port': port, 'market_id':
                self.id, 'orderstore': OrderStore(self.id, 0)}
            investor_state = LEEPSInvestorState(**fields)
            self.investor = LEEPSInvestor(investor_state)
        self.investor.invest(**kwargs)
        while self.investor.outgoing_messages:
            message = self.investor.outgoing_messages.popleft()
            self.outgoing_messages.append(message)
           
    def system_event(self, **kwargs):
        event_code = kwargs.get('event_code')
        broadcast_info = ('batch', {'event': event_code})
        self.broadcast_to_subscribers(broadcast_info)   


class LEEPSMarket(BCSMarket):

    def __init__(self, order_imbalance_function, **kwargs):
        super().__init__(**kwargs)
        self.order_imbalance = next(order_imbalance_function)
        self.role_groups = {'maker_basic':[], 'maker_latent': [], 'taker': []}
    
    def role_change(self, new_role:str, old_role:str, player_id:str, **kwargs):
        if new_role not in self.roles:
            raise KeyError('invalid role: %s' % new_role)
        self.role_groups[new_role].append(player_id)
        if old_role in self.role_groups:
            self.role_groups[old_role].pop(player_id)
    
    def order_imbalance_change(self, order_imbalance_function=order_imbalance_function,
            **kwargs):
        buy_sell_indicator = kwargs.get('buy_sell_indicator')
        current_order_imbalance = order_imbalance_function.send(buy_sell_indicator)
        if current_order_imbalance != self.order_imbalance:
            self.order_imbalance = current_order_imbalance
        maker_ids = self.role_groups['maker_latent']
        message_content = {
            'type':'order_imbalance_change', 
            'order_imbalance': current_order_imbalance, 
            'maker_ids': maker_ids}
        internal_message = format_message('market', **message_content)
        self.outgoing_messages.append(internal_message)

    def bbo_update(self, **kwargs):
        all_maker_ids = itertools.chain(self.role_groups['maker_basic'], 
            self.role_groups['maker_latent'])
        message_content = {'type': 'bbo_change', 'order_imbalance': self.order_imbalance, 
            'maker_ids': all_maker_ids}
        internal_message = format_message('market', **message_content)
        self.outgoing_messages.append(internal_message)
        best_bid, best_offer = kwargs['best_bid'], kwargs['best_offer']
        broadcast_info = ('bbo', {'best_bid': best_bid, 'best_offer': best_offer})
        self.broadcast_to_subscribers(broadcast_info)
        

         


        









