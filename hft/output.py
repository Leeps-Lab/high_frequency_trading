from otree.api import models
from otree.db.models import Model, ForeignKey
from . import market_environments
from django.utils import timezone
import logging

log = logging.getLogger(__name__)



class TimeAwareInSessionRecord(Model):
    timestamp = models.DateTimeField(default=timezone.now)
    trigger_event_type = models.CharField()
    event_no = models.IntegerField()
    subsession_id = models.IntegerField()
    market_id = models.IntegerField()


class TraderRecord(TimeAwareInSessionRecord):
    
    csv_meta = (
    'timestamp', 'subsession_id', 'market_id', 'player_id', 'trigger_event_type',
    'event_no',  'trader_model_name', 'inventory', 'bid', 'offer', 
    'best_bid_except_me', 'best_offer_except_me',
    'delay', 'speed', 'staged_bid', 'staged_offer', 'implied_bid', 
    'implied_offer', 'slider_a_x','slider_a_y', 'slider_a_z',
    'net_worth', 'cash', 'tax_paid', 'speed_cost', 'midpoint_peg', 'peg_price', 'peg_state',
    'avgLatency', 'maxLatency', 'reference_price', 'executed_price', 'buy_sell_indicator')

    # timestamp = models.DateTimeField(default=timezone.now)
    # trigger_event_type = models.CharField()
    # event_no = models.IntegerField()
    # subsession_id = models.IntegerField()
    # market_id = models.IntegerField()
    player_id = models.IntegerField()
    trader_model_name =  models.CharField()
    delay = models.FloatField()
    net_worth = models.IntegerField()
    cash = models.IntegerField()
    cost = models.IntegerField()
    speed_cost = models.IntegerField()
    tax_paid = models.IntegerField()
    reference_price = models.IntegerField()
    inventory = models.IntegerField()
    bid = models.IntegerField()
    offer = models.IntegerField()
    staged_bid = models.IntegerField()
    staged_offer = models.IntegerField()
    implied_bid = models.IntegerField()
    implied_offer = models.IntegerField()
    best_bid = models.IntegerField()
    best_offer = models.IntegerField()
    best_bid_except_me = models.IntegerField()
    best_offer_except_me = models.IntegerField()
    next_bid = models.IntegerField()
    next_offer = models.IntegerField()
    volume_at_best_bid = models.IntegerField()
    volume_at_best_offer = models.IntegerField()
    e_best_bid = models.IntegerField()
    e_best_offer = models.IntegerField()
    slider_a_x = models.FloatField()
    slider_a_y = models.FloatField()
    slider_a_z = models.FloatField()
    signed_volume = models.FloatField()
    e_signed_volume = models.FloatField()
    midpoint_peg = models.BooleanField()
    peg_price = models.IntegerField()
    peg_state = models.IntegerField()
    
    total_bids = models.IntegerField()
    total_asks = models.IntegerField()
    sum_bid_price = models.IntegerField()
    sum_ask_price = models.IntegerField()

    executed_price = models.IntegerField()
    buy_sell_indicator = models.CharField()

    # Used to measure latency
    avgLatency = models.FloatField()
    maxLatency = models.FloatField()

class MarketRecord(TimeAwareInSessionRecord):

    csv_meta = (
    'timestamp', 'subsession_id', 'market_id', 'player_id', 'trigger_event_type',
    'event_no',  'reference_price', 'best_bid', 'best_offer', 
    'next_bid', 'next_offer', 'volume_at_best_bid', 'volume_at_best_offer', 
    'e_best_bid', 'e_best_offer', 'signed_volume', 'e_signed_volume', 'clearing_price', 'transacted_volume')

    reference_price = models.IntegerField()
    best_bid = models.IntegerField()
    best_offer = models.IntegerField()
    next_bid = models.IntegerField()
    next_offer = models.IntegerField()
    volume_at_best_bid = models.IntegerField()
    volume_at_best_offer = models.IntegerField()
    e_best_bid = models.IntegerField()
    e_best_offer = models.IntegerField()
    signed_volume = models.FloatField()
    e_signed_volume = models.FloatField()
    clearing_price = models.IntegerField()
    transacted_volume = models.IntegerField()

def get_required_model_fields(session_format, model_name):
    market_env = market_environments.environments[session_format].checkpoint[model_name]
    req_props = market_env['properties_to_serialize']
    req_subprops = market_env['subproperties_to_serialize']
    return req_props, req_subprops

IN_SESSION_RECORD_CLASSES={'trader': TraderRecord, 'market': MarketRecord,
                'inv': TraderRecord}
def checkpoint(serialized_model: dict, session_format, model_name, 
               event_type='', event_no=None, market_environments=market_environments):
    def ensure_valid_kws(record_cls, kwas: dict):
        keys = list(kwas.keys())
        fields_names = [f.name for f in record_cls._meta.fields]
        for k in keys:
            if k not in fields_names:
                del kwas[k]
        return kwas
    record_class = IN_SESSION_RECORD_CLASSES[model_name]
    kws = ensure_valid_kws(record_class, serialized_model)
    # hack: only show clearing price and volume on a batch message
    if 'clearing_price' in kws and event_type != 'Z':
        del kws['clearing_price']
        del kws['transacted_volume']
    record = record_class.objects.create(trigger_event_type=event_type,
        event_no=event_no, **kws)
    return record