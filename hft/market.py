from .market_elements.market_role import MarketRoleGroup
from .market_facts import BestBidOffer, ELOExternalFeed, ReferencePrice, SignedVolume
from .utility import nanoseconds_since_midnight, MIN_BID, MAX_ASK
import logging
from datetime import datetime
from django.utils.timezone import utc


log = logging.getLogger(__name__)


class MarketFactory:
    @staticmethod
    def get_market(session_format):
        if session_format == 'elo':
            return ELOMarket
        else:
            raise ValueError('unknown format %s' % session_format)


class BaseMarket:
    market_events_dispatch = {}
    session_format = None
    model_name = 'market'
    mark_events_with_props = ()
    mark_events_with_stats = ()

    def __init__(self, group_id, id_in_subsession, subsession_id, exchange_host, 
                 exchange_port, **kwargs):
        self.market_id = group_id
        self.id_in_subsession = id_in_subsession
        self.subsession_id = subsession_id
        self.exchange_host = exchange_host 
        self.exchange_port = exchange_port
        self.is_trading = False
        self.ready_to_trade = False
        self.players_in_market = {}
        self.time_session_start = None
        self.time_session_end = None
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)

    def register_player(self, group_id, player_id):
        self.players_in_market[player_id] = False
    
    def handle_event(self, event, *args, **kwargs):
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
            attachments = {}
            for prop in self.mark_events_with_props:
                attachments[prop] = getattr(self, prop)
            for subprop in self.mark_events_with_stats:
                market_stat = getattr(self, subprop)
                attachments.update(market_stat.to_kwargs())
            self.event.attach(**attachments)
            self.event = None
     
    def start_trade(self, *args, **kwargs):
        if not self.ready_to_trade:
            raise ValueError('market %s not ready not trade.' % self.market_id)
        else:
            if self.is_trading:
                raise ValueError('market %s already trading.' % self.market_id)
            else:
                self.is_trading = True
                self.event.broadcast_msgs('system_event', model=self, code='S')
        self.time_session_start = datetime.utcnow().replace(tzinfo=utc)

    def end_trade(self, *args, **kwargs):
        self.is_trading = False
        self.time_session_end = datetime.utcnow().replace(tzinfo=utc)

    def player_ready(self, **kwargs):
        player_id = int(kwargs['player_id'])
        self.players_in_market[player_id] = True
        market_ready_condition = (
            True if False not in self.players_in_market.values() else False)
        if market_ready_condition is True:
            self.ready_to_trade = True
            self.event.internal_event_msgs('market_ready_to_start', model=self)

    def system_event(self, **kwargs):
        pass


class ELOMarket(BaseMarket):
    session_format = 'elo'
    market_events_dispatch = {
        'E': ('signed_volume_change', 'reference_price_change'),
        'role_change': 'role_change',
        'player_ready': 'player_ready',
        'S': 'system_event',
        'market_start': 'start_trade',
        'market_end': 'end_trade',
        'Q': 'bbo_change',
        'Z': 'post_batch',
        'external_feed': 'external_feed_change'} 
    mark_events_with_props = (
        'tax_rate', 'time_session_start', 'time_session_end')
    mark_events_with_stats = ('bbo', 'signed_volume', 'external_feed', 'reference_price')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bbo = BestBidOffer()
        self.external_feed = ELOExternalFeed()
        self.signed_volume = SignedVolume(**kwargs) 
        self.reference_price = ReferencePrice(**kwargs)
        self.role_group = MarketRoleGroup('manual', 'automated', 'out')
        self.tax_rate = kwargs.get('tax_rate', 0)
    
    def start_trade(self, *args, **kwargs): 
        super().start_trade(*args, **kwargs)
        for time_aware_stat in ('signed_volume', 'reference_price'):
            attr = getattr(self, time_aware_stat)
            attr.reset_timer()
        # next is not really ok. 
        # will change later.
        for pid in self.players_in_market.keys():
            self.role_group.update(nanoseconds_since_midnight(), pid, 'out')

    def end_trade(self, *args, **kwargs):
        super().end_trade(*args, **kwargs)
        for pid in self.players_in_market.keys():
            self.role_group.update(nanoseconds_since_midnight(), pid, 'out')

    def role_change(self, *args, **kwargs):
        player_id, new_role = kwargs['player_id'], kwargs['state']
        self.role_group.update(nanoseconds_since_midnight(), player_id, new_role)

    def reference_price_change(self, **kwargs):
        self.reference_price.update(**kwargs)
        if self.reference_price.has_changed:
            self.event.broadcast_msgs(
                'reference_price', market_id=self.market_id, 
                **self.reference_price.to_kwargs())
            self.event.internal_event_msgs(
                'reference_price_change', model=self, 
                **self.reference_price.to_kwargs())
    
    def signed_volume_change(self, **kwargs):
        kwargs.update(self.bbo.to_kwargs())
        self.signed_volume.update(**kwargs)
        if self.signed_volume.has_changed:
            # maker_ids = self.role_group['automated', 'manual', 'out']
            self.event.internal_event_msgs(
                'signed_volume_change',
                model=self, **self.signed_volume.to_kwargs())
            self.event.broadcast_msgs('signed_volume', model=self, 
                **self.signed_volume.to_kwargs())
        
    def bbo_change(self, **kwargs):
        self.bbo.update(**kwargs)
        if self.bbo.has_changed:
            # hft_traders = self.role_group['automated', 'manual', 'out']
            self.event.internal_event_msgs(
                'bbo_change', model=self, **self.bbo.to_kwargs())
            self.event.broadcast_msgs('bbo', model=self, **self.bbo.to_kwargs())

    def post_batch(self, **kwargs):
        self.bbo.update(**kwargs)
        if self.bbo.has_changed:
            self.event.internal_event_msgs(
                'post_batch', model=self, **self.bbo.to_kwargs())
            self.event.broadcast_msgs('post_batch', model=self, **self.bbo.to_kwargs())
    
    def external_feed_change(self, **kwargs):
        self.external_feed.update(**kwargs)
        if self.external_feed.has_changed:
            hft_traders = self.role_group['automated', 'manual', 'out']
            self.event.internal_event_msgs(
                'external_feed_change', model=self, trader_ids=hft_traders, **self.external_feed.to_kwargs())
            self.event.broadcast_msgs('external_feed', model=self, **self.external_feed.to_kwargs())

        










