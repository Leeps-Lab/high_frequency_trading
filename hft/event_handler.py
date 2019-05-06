from .cache import (
    model_key_format_str_kw, lock_key_format_str, get_trader_ids_by_market)
from django.core.cache import cache
from otree.timeout.tasks import hft_background_task
from random import shuffle
from .trader import TraderFactory
import logging
from .output import trader_checkpoint

log = logging.getLogger(__name__)


class EventHandler(object):

    model_id_field_name = None
    model_name = None

    def __init__(self, event, market_environment, state_serializer=None):
        self.market_environment = market_environment
        self.model_id = getattr(event, self.model_id_field_name)
        self.event = event
        self.model_cache_key = model_key_format_str_kw.format(
            model_id=self.model_id, model_name=self.model_name,
            subsession_id=event.subsession_id)
        self.cache_lock_key = lock_key_format_str.format(cache_key=self.model_cache_key)
        self.state_serializer = state_serializer

    def read_model(self, **kwargs):
        model = cache.get(self.model_cache_key)
        if model is None:
            raise Exception('cache key: {self.model_cache_key} returned none,'
                      'event: {self.event}'.format(self=self))
        else:
            self.model = model

    def handle(self, **kwargs):
        with cache.lock(self.cache_lock_key):
            self.read_model(**kwargs)
            self.model.handle_event(self.event)
            self.post_handle()
            cache.set(self.model_cache_key, self.model)
        return self.event
    
    def post_handle(self, **kwargs):
        pass


class TraderPostHandleMixIn:

    # so I dont duplicate code
    def post_handle(self):
        hft_background_task(self.state_serializer, self.model, 
                            self.market_environment, 
                            event_type=self.event.event_type,
                            event_no=self.event.reference_no)


class TraderEventHandler(TraderPostHandleMixIn, EventHandler):

    model_id_field_name = 'player_id'
    model_name = 'trader'


class MarketEventHandler(EventHandler):

    model_id_field_name = 'market_id'
    model_name = 'market'


class InvestorEventHandler(TraderPostHandleMixIn, EventHandler):

    model_id_field_name = 'market_id'
    model_name = 'inv'



SUBPROCESSES = {}


class TradeSessionEventHandler(EventHandler):

    model_id_field_name = 'subsession_id'
    model_name = 'trade_session'
    background_logger = None

    def read_model(self, **kwargs):
        super().read_model(**kwargs)
        subs_id = self.model.subsession_id
        if subs_id not in SUBPROCESSES:
            SUBPROCESSES[subs_id] = {}
        self.model.clients = SUBPROCESSES[subs_id]

    def post_handle(self, *kwargs):
        super().post_handle()
        SUBPROCESSES[self.model.subsession_id] = self.model.clients
        self.model.clients = {}


class MarketWideEventHandler:

    def __init__(self, event, market_environment, **kwargs):
        self.event = event
        self.kwargs = kwargs
        self.market_environment = market_environment

    def handle(self, **kwargs):
        try:
            responding_trader_ids = self.event.message.trader_ids
        except AttributeError:
            responding_trader_ids = get_trader_ids_by_market(
                self.event.market_id, self.event.subsession_id)
        if responding_trader_ids:
            for trader_id in responding_trader_ids:
                self.event.player_id = trader_id
                handler = TraderEventHandler(self.event, self.market_environment)
                handler.handle()
        shuffle(self.event.outgoing_messages)
        return self.event

def is_investor(event):
    return (hasattr(event.message, 'token_prefix') and event.message.token_prefix == 'inv') or (
            event.message.type == 'investor_arrivals')

class EventHandlerFactory:

    @staticmethod
    def get_handler(event, topic, market_environment, **kwargs):
        if topic == 'market':
            return MarketEventHandler(event, market_environment, **kwargs)
        elif topic == 'trader':
            if is_investor(event):
                return InvestorEventHandler(event, market_environment, **kwargs)
            else:
                return TraderEventHandler(event, market_environment, **kwargs)
        elif topic == 'trade_session':
            return TradeSessionEventHandler(event, market_environment, **kwargs)
        elif topic == 'marketwide_events':
            return MarketWideEventHandler(event, market_environment, **kwargs)
        else:
            raise Exception('invalid topic: %s' % topic)
