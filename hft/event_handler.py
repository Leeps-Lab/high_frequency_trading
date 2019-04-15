from .cache import model_key_format_str_kw, lock_key_format_str
from django.core.cache import cache
from otree.timeout.tasks import hft_background_task
from . import checkpoints
from random import shuffle
import logging
from .subject_state import SubjectStateFactory
from .trader import TraderFactory 

log = logging.getLogger(__name__)


class EventHandler:

    model_name = None
    background_logger = None

    def __init__(self, event, model_id, model_name=model_name, 
                 market_environment=''):
        self.market_environment = market_environment
        self.model_id = model_id
        self.model_type = model_type
        self.event = event
        self.model_cache_key = model_key_format_str_kw.format(
            model_id=model_id, model_name=model_name,
            subssession_id=event.subssession_id)
        self.cache_lock_key = lock_key_format_str.format(self.model_cache_key)

    def read_model(self):
        model = cache.get(self.model_cache_key)
        if model is None:
            Exception('cache key: {self.model_cache_key} returned none,'
                      'event: {self.event}'.format(self=self))
        else:
            self.model = model

    def handle(self, **kwargs):
        with cache.lock(self.cache_lock_key):
            self.read_model(model_data)
            message_queue = self.model.outgoing_messages.copy()
            self.model.receive(self.event)
            self.model.outgoing_messages.clear()
            self.event.outgoing_messages.extend(message_queue)
            self.post_handle()
            cache.set(self.model_cache_key, self.model)

    def post_handle(self, **kwargs):
        if self.background_logger is not None:
            hft_background_task(self.background_logger, self.model, self.event.to_kwargs())


class TraderEventHandler(EventHandler):

    model_name = 'trader'
    background_logger = checkpoints.hft_trader_checkpoint


class TraderRoleChangeEventHandler(EventHandler):
    # 'role_change' has its own code spec.
    # as it changes the trader implementation

    model_name = 'trader'
    background_logger = checkpoints.hft_trader_checkpoint

    def read_model(self):
        super().read_model()
        trader_state_cls = SubjectStateFactory.get_state(
            self.market_environment) 
        trader_state = trader_state_cls.from_trader(self.model)
        new_role = event.get_new_role()
        trader = TraderFactory(
            self.market_environment, new_role, subject_state)
        self.model = trader
        

class MarketEventHandler(EventHandler):

    model_name = 'market'
    background_logger = None


class InvestorEventHandler(EventHandler):

    model_name = 'investor'
    background_logger = None


SUBPROCESSES = {}


class TradeSessionEventHandler(EventHandler):

    model_name = 'trade_session'
    background_logger = None

    def read_model(self):
        super().read_model()
        subs_id = self.model.subsession_id
        if subs_id not in SUBPROCESSES:
            SUBPROCESSES[subs_id] = {}
        self.model.clients = SUBPROCESSES[subs_id]

    def post_handle(self, *kwargs):
        super().post_handle()
        SUBPROCESSES[self.model.subsession_id] = self.model.clients
        self.model.clients = {}



class MarketWideEventHandler:

    @staticmethod
    def handle(event, **kwargs):
        try:
            responding_trader_ids = event.message.trader_ids
        except AttributeError:
            responding_trader_ids = get_trader_ids_by_market(event.market_id)
        if responding_trader_ids:
            for trader_id in responding_trader_ids:
                handler = TraderEventHandler(event, trader_id)
                event = handler.handle()
        shuffle(event.outgoing_messages)
