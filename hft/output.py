from otree.api import models
from otree.db.models import Model, ForeignKey
from . import market_environments
from django.utils import timezone
import logging

log = logging.getLogger(__name__)


class InSessionTraderRecord(Model):
    
    csv_meta = (
    'timestamp', 'subsession_id', 'market_id', 'player_id', 'trigger_event_type',
    'net_worth', 'cash', 'tax_paid', 'speed_cost', 'trader_model_name', 'inventory', 'reference_price', 
    'bid', 'offer', 'best_bid', 'best_offer', 'e_best_bid', 'e_best_offer', 
    'staged_bid', 'staged_offer', 'implied_bid', 'implied_offer', 'slider_a_x',
    'slider_a_y', 'slider_a_z', 'signed_volume', 'e_signed_volume')

    timestamp = models.DateTimeField(default=timezone.now)
    trigger_event_type = models.CharField()
    event_no = models.IntegerField()
    subsession_id = models.IntegerField()
    market_id = models.IntegerField()
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
    e_best_bid = models.IntegerField()
    e_best_offer = models.IntegerField()
    slider_a_x = models.FloatField()
    slider_a_y = models.FloatField()
    slider_a_z = models.FloatField()
    signed_volume = models.FloatField()
    e_signed_volume = models.FloatField()
 
def serialize_in_memo_model(in_memo_model, req_props, req_subprops: dict):
    # assumes no clash in tuple elements and dict keys
    result = {}
    for prop_name in req_props: 
        value = getattr(in_memo_model, prop_name)
        if value is not None:
            result[prop_name] = value
    for prop_name, subprop_names in req_subprops.items():
        attr = getattr(in_memo_model, prop_name)
        if attr is not None:
            for subprop_name in subprop_names:
                if isinstance(attr, dict):
                    value = attr[subprop_name]
                elif hasattr(attr, subprop_name):
                    value = getattr(attr, subprop_name)
                    # maybe it is a dictionary
                else:
                    raise AttributeError('%s has no %s:%s' % (attr, prop_name, subprop_name))
                result[subprop_name] = value
    return result
   
def get_required_model_fields(market_environment):
    market_env = market_environments.environments['elo'].checkpoint
    req_props = market_env['properties_to_serialize']
    req_subprops = market_env['subproperties_to_serialize']
    return req_props, req_subprops

def trader_checkpoint(serialized_model: dict, session_format, event_type='', event_no=None,
                       market_environments=market_environments):
    def ensure_valid_kws(record_cls, kwas: dict):
        keys = list(kwas.keys())
        fields_names = [f.name for f in record_cls._meta.fields]
        for k in keys:
            if k not in fields_names:
                del kwas[k]
        return kwas
    kws = ensure_valid_kws(InSessionTraderRecord, serialized_model)
    record = InSessionTraderRecord.objects.create(trigger_event_type=event_type,
        event_no=event_no, **kws)
    return record