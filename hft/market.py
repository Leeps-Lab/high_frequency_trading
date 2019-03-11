
import logging
from collections import deque
import itertools
import math
from .subject_state import SubjectStateFactory
from .orderstore import OrderStore
from .utility import format_message, MIN_BID, MAX_ASK
from .cache import initialize_player_cache
from .equations import OrderImbalance, ReferencePrice
from .market_components.market_role import MarketRoleGroup
from .utility import nanoseconds_since_midnight
log = logging.getLogger(__name__)

class MarketFactory:
    @staticmethod
    def get_market(session_format):
        if session_format == 'BCS':
            return BCSMarket
        elif session_format == 'elo':
            return ELOMarket
        else:
            raise ValueError('unknown format %s' % session_format)

class BaseMarket:
    market_events_dispatch = {}
    _ids = itertools.count(1,1)
    state_factory = SubjectStateFactory
    session_format = None
    tag_all_events_with = ()

    def __init__(self, id_in_subsession, subsession_id, exchange_host, exchange_port, **kwargs):
        self.id_in_subsession = id_in_subsession
        self.subsession_id = subsession_id
        self.exchange_address = (exchange_host, exchange_port)
        self.market_id = str(next(self._ids))
        self.is_trading = False
        self.ready_to_trade= False
        self.subscribers = {}
        self.players_in_market = {}

        self.attachments_for_observers = {}
        self.outgoing_messages = deque()

    def register_player(self, group_id, player_id):
        if group_id not in self.subscribers.keys():
            self.subscribers[group_id] = []
        self.subscribers[group_id].append(player_id)
        self.players_in_market[player_id] = False
    
    def receive(self, event, *args, **kwargs):
        if event.event_type not in self.market_events_dispatch:
            raise KeyError('unknown market event.')
        else:
            self.event = event
            handler_info = self.market_events_dispatch[event.event_type]
            kws = event.to_kwargs()
            if isinstance(handler_info, tuple):
                for handler_name in handler_info:
                    handler = getattr(self, handler_name)
                    handler(*args, **kws)
            if isinstance(handler_info, str):
                    handler = getattr(self, handler_info)
                    handler(*args, **kws)
            for field in self.tag_all_events_with:
                event.attachments[field] = getattr(self, field)
            self.event = None
     
    def start_trade(self, *args, **kwargs):
        if not self.ready_to_trade:
            raise ValueError('market %s not ready not trade.' % self.market_id)
        else:
            if self.is_trading:
                raise ValueError('market %s already trading.' % self.market_id)
            else:
                self.is_trading = True
                self.event.broadcast_messages('system_event', model=self, code='S')

        
    
    def end_trade(self, *args, **kwargs):
        if self.is_trading:
            self.is_trading = False

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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key in kwargs.keys():
            setattr(self, key, kwargs.get(key))
        self.roles = ('maker', 'sniper', 'out')
        self.role_counts = {role: 0 for role in self.roles}
        self.investor = None

    def player_ready(self, **kwargs):
        player_id = int(kwargs.get('player_id'))
        self.players_in_market[player_id] = True
        market_ready_condition = (True if False not in self.players_in_market.values() 
            else False)
        if market_ready_condition is True:
            self.ready_to_trade = True
            message_content = {'type': 'market_ready_to_start', 'market_id': self.market_id,
                'subsession_id': self.subsession_id}
            internal_message = format_message('derived_event', **message_content)
            self.outgoing_messages.append(internal_message)
    
    def player_reached_session_end(self, **kwargs):
        player_id = int(kwargs.get('player_id'))
        self.players_in_market[player_id] = False
        message_content = {'type': 'market_ready_to_end', 'market_id': self.market_id,
                'subsession_id': self.subsession_id}
        internal_message = format_message('derived_event', **message_content)
        self.outgoing_messages.append(internal_message)

    def fundamental_price_change(self, **kwargs):
        new_fp = int(kwargs['new_fundamental'])
        self.fp = new_fp
        self.event.broadcast_messages('fundamental_price_change', new_price=new_fp)

    def system_event(self, **kwargs):
        pass

max_ask = 2147483647
min_bid = 0

class ELOMarket(BCSMarket):
    session_format = 'elo'

    market_events_dispatch = {
        'E': ('order_imbalance_change', 'reference_price_change'),
        'role_change': 'role_change',
        'player_ready': 'player_ready',
        'advance_me': 'player_reached_session_end',
        'S': 'system_event',
        'market_start': 'start_trade',
        'market_end': 'end_trade',
        'Q': 'bbo_change'
    }
    tag_all_events_with = ('best_bid', 'best_offer', 'volume_at_best_bid', 
        'volume_at_best_offer', 'order_imbalance', 'reference_price', 'tax_rate')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_format = 'elo'
        self.best_bid = min_bid
        self.volume_at_best_bid = 0
        self.best_offer = max_ask
        self.volume_at_best_offer = 0
        self.order_imbalance = 0
        self.reference_price = ReferencePrice(math.log(2))
        self.tax_rate = 0
        self.role_group = MarketRoleGroup('manual', 'maker', 'taker', 'out')
    
    def start_trade(self, *args, **kwargs):
        super().start_trade(*args, **kwargs)
        session_duration = kwargs['session_length']
        self.reference_price.start(session_duration=session_duration)

    def role_change(self, *args, **kwargs):
        player_id = kwargs['player_id']
        new_role = kwargs['state']
        self.role_group.update(nanoseconds_since_midnight(), player_id, new_role)

    def reference_price_change(self, **kwargs):
        price = kwargs['execution_price']
        reference_price = self.reference_price.step(price)
        self.event.broadcast_messages('reference_price', market_id=self.market_id, 
            price=reference_price)
    
    def order_imbalance_change(self, order_imbalance=OrderImbalance(), **kwargs):
        buy_sell_indicator = kwargs.get('buy_sell_indicator')
        execution_price = kwargs['execution_price']
        current_order_imbalance = order_imbalance.step(execution_price, self.best_bid, 
            self.best_offer, buy_sell_indicator)
        if current_order_imbalance != self.order_imbalance:
            current_order_imbalance = round(current_order_imbalance, 2)
            self.order_imbalance = current_order_imbalance
            maker_ids = self.role_group['maker', 'taker']
            message_content = {
                'type':'order_imbalance_change', 
                'order_imbalance': current_order_imbalance, 
                'trader_ids': maker_ids,
                'market_id': self.market_id,
                'subsession_id': self.subsession_id}
            internal_message = format_message('derived_event', **message_content)
            self.outgoing_messages.append(internal_message)
            self.event.broadcast_messages('order_imbalance', model=self, 
                value=current_order_imbalance)
        
    def bbo_change(self, **kwargs):
        self.volume_at_best_bid = kwargs['volume_at_best_bid']
        self.volume_at_best_offer = kwargs['volume_at_best_ask']
        self.best_bid, self.best_offer = kwargs['best_bid'], kwargs['best_ask']
        maker_ids = self.role_group['maker', 'taker']
        message_content = {'type': 'bbo_change', 'order_imbalance': self.order_imbalance, 
            'market_id': self.market_id, 'best_bid': self.best_bid, 'best_offer': self.best_offer,
            'trader_ids': maker_ids, 'volume_at_best_bid': self.volume_at_best_bid,
            'volume_at_best_offer': self.volume_at_best_offer, 'subsession_id': self.subsession_id}
        internal_message = format_message('derived_event', **message_content)
        self.outgoing_messages.append(internal_message)
        self.event.broadcast_messages('bbo', model=self)
        










