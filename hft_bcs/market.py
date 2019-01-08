
import logging
from collections import deque
import itertools
from .trader import LEEPSInvestor
from .subject_state import LEEPSInvestorState
from .orderstore import OrderStore
from .utility import format_message, MIN_BID, MAX_ASK

from .equations import OrderImbalance
log = logging.getLogger(__name__)

class MarketFactory:
    @staticmethod
    def get_market(session_format):
        if session_format == 'BCS':
            return BCSMarket
        elif session_format == 'LEEPS':
            return LEEPSMarket

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
    
 
    def add_exchange(self, host, port):
        self.exchange_address = (host, port)
    
    def register_session(self, subsession_id):
        self.subsession_id = subsession_id
    
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
            attachments = handler(*args, **kwargs)
            return attachments
    
    def broadcast_to_subscribers(self, broadcast_info):
        topic, data = broadcast_info
        # for group_id in self.subscriber_groups.keys():
        message_content = { 'group_id': self.id, 'type': topic, 
        'message': data}
        internal_message = format_message('broadcast', **message_content)            
        self.outgoing_messages.append(internal_message)
     
    def start_trade(self, *args, **kwargs):
        if not self.ready_to_trade:
            raise ValueError('market %s not ready not trade.' % self.id)
        else:
            if self.is_trading:
                raise ValueError('market %s already trading.' % self.id)
            else:
                self.is_trading = True
                broadcast_info = ('session_start', {})
                self.broadcast_to_subscribers(broadcast_info)
    
    def end_trade(self, *args, **kwargs):
        if self.is_trading:
            self.is_trading = False

    def __len__(self):
        return len(self.subscriber_groups)

class BCSMarket(BaseMarket):
    market_events_dispatch = {
        'fundamental_value_jumps': 'fundamental_price_change',
        'investor_arrivals': 'noise_trader_arrival',
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
        player_id = int(kwargs.get('player_id'))
        self.players_in_market[player_id] = True
        market_ready_condition = (True if False not in self.players_in_market.values() 
            else False)
        if market_ready_condition is True:
            self.ready_to_trade = True
            message_content = {'type': 'market_ready_to_start', 'market_id': self.id,
                'subsession_id': self.subsession_id}
            internal_message = format_message('derived_event', **message_content)
            self.outgoing_messages.append(internal_message)
    
    def player_reached_session_end(self, **kwargs):
        player_id = int(kwargs.get('player_id'))
        self.players_in_market[player_id] = False
        message_content = {'type': 'market_ready_to_end', 'market_id': self.id,
                'subsession_id': self.subsession_id}
        internal_message = format_message('derived_event', **message_content)
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

    market_events_dispatch = {
        'E':'order_imbalance_change',
        'role_change': 'role_change',
        'fundamental_value_jumps': 'fundamental_price_change',
        'investor_arrivals': 'noise_trader_arrival',
        'player_ready': 'player_ready',
        'advance_me': 'player_reached_session_end',
        'S': 'system_event',
        'market_start': 'start_trade',
        'market_end': 'end_trade',
        'Q': 'bbo_change'
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.order_imbalance = 0
        self.best_bid = MIN_BID
        self.best_offer = MAX_ASK
        self.role_groups = {'maker': [], 'maker_basic':[], 'maker_latent': [], 
            'sniper':[], 'taker': [], 'out': []}

    def role_change(self, **kwargs):
        player_id = kwargs['player_id']
        new_role = kwargs['state'].lower()
        if new_role not in self.role_groups:
            raise KeyError('invalid role: %s for market type: %s' % (new_role, 
                self.__class__.__name__))
        self.role_groups[new_role].append(player_id)
        old_role = None
        for k, v in self.role_groups.items():
            if player_id in v:
                old_role = k
                break
        if old_role:
            self.role_groups[old_role].remove(player_id)
        if new_role in ('maker_basic'):
            return {'best_bid': self.best_bid, 'best_offer': self.best_offer,
                'order_imbalance': self.order_imbalance}
    
    def order_imbalance_change(self, order_imbalance=OrderImbalance(), **kwargs):
        buy_sell_indicator = kwargs.get('buy_sell_indicator')
        current_order_imbalance = order_imbalance.step(buy_sell_indicator)
        if current_order_imbalance != self.order_imbalance:
            self.order_imbalance = current_order_imbalance
        maker_ids = self.role_groups['maker_latent']
        message_content = {
            'type':'order_imbalance_change', 
            'order_imbalance': current_order_imbalance, 
            'maker_ids': maker_ids,
            'market_id': self.id,
            'subsession_id': self.subsession_id}
        internal_message = format_message('derived_event', **message_content)
        self.outgoing_messages.append(internal_message)

    def bbo_change(self, **kwargs):
        best_bid, best_offer = kwargs['best_bid'], kwargs['best_ask']
        self.best_bid = best_bid
        self.best_offer = best_offer
        message_content = {'type': 'bbo_change', 'order_imbalance': self.order_imbalance, 
            'market_id': self.id, 'best_bid': best_bid, 'best_offer': best_offer,
            'subsession_id': self.subsession_id}
        internal_message = format_message('derived_event', **message_content)
        self.outgoing_messages.append(internal_message)
        broadcast_info = ('bbo', {'best_bid': best_bid, 'best_offer': best_offer})
        self.broadcast_to_subscribers(broadcast_info)
        

         


        









