from otree.api import models
from otree.db.models import Model, ForeignKey
from . import market_environments
from django.utils import timezone
import logging

log = logging.getLogger(__name__)


def serialize_in_memo_model(in_memo_model, req_subprops=None):
    # assumes no name clash in tuple elements and dict keys
    result = {}
    for prop_name in in_memo_model.__class__.__slots__:
        value = getattr(in_memo_model, prop_name)
        if value is not None:
            result[prop_name] = value
    for prop_name, subprop_names in req_subprops.items():
        attr = getattr(in_memo_model, prop_name)
        if attr is not None:
            for subprop_name in subprop_names:
                value = getattr(attr, subprop_name)
                result[subprop_name] = value
    return result


class ELOInSessionTraderRecord(Model):
    
    csv_meta = (
    'timestamp', 'subsession_id', 'market_id', 'player_id', 'trigger_event_type',
    'wealth', 'cash', 'technology_cost', 'role', 'speed_on', 'time_on_speed', 
    'inventory', 'reference_price',
    'bid', 'offer', 'best_bid', 'best_offer', 'e_best_bid', 'e_best_offer', 
    'target_bid', 'target_offer', 'implied_bid', 'implied_offer', 'slider_a_x',
    'slider_a_y', 'slider_a_z', 'signed_volume', 'e_signed_volume')

    timestamp = models.DateTimeField(default=timezone.now)
    trigger_event_type = models.StringField()
    event_no = models.IntegerField()
    subsession_id = models.CharField()
    market_id = models.IntegerField()
    player_id = models.IntegerField()
    wealth = models.IntegerField(default=0)
    cash = models.IntegerField(default=0)
    technology_cost = models.IntegerField(initial=0)
    tax = models.IntegerField(blank=True)
    role =  models.StringField()
    speed_on = models.BooleanField()
    time_on_speed = models.IntegerField()
    reference_price = models.IntegerField(blank=True)
    inventory = models.IntegerField()
    bid = models.IntegerField(blank=True)
    offer = models.IntegerField(blank=True)
    target_bid = models.IntegerField(blank=True)
    target_offer = models.IntegerField(blank=True)
    implied_bid = models.IntegerField(blank=True)
    implied_offer = models.IntegerField(blank=True)
    best_bid = models.IntegerField(blank=True)
    best_offer = models.IntegerField(blank=True)
    e_best_bid = models.IntegerField(blank=True)
    e_best_offer = models.IntegerField(blank=True)
    slider_a_x = models.FloatField(blank=True)
    slider_a_y = models.FloatField(blank=True)
    slider_a_z = models.FloatField(blank=True)
    signed_volume = models.FloatField(blank=True)
    e_signed_volume = models.FloatField(blank=True)


IN_SESSION_STATE_MODELS = {
    '1': ELOInSessionTraderRecord
}


def trader_checkpoint(in_memo_model, session_format, event_type='', event_no=None,
                       market_environments=market_environments):
    def ensure_valid_kws(record_cls, kwas: dict):
        keys = list(kwas.keys())
        fields_names = [f.name for f in record_cls._meta.fields]
        for k in keys:
            if k not in fields_names:
                del kwas[k]
        return kwas
    market_env = market_environments.environments[session_format]
    req_subpros = market_env.checkpoint['subproperties_to_serialize']
    kws = serialize_in_memo_model(in_memo_model, req_subprops=req_subpros)
    record_model_code = market_env.checkpoint['record_model_code']
    record_cls = IN_SESSION_STATE_MODELS[record_model_code]
    kws = ensure_valid_kws(record_cls, kws)
    record = record_cls.objects.create(trigger_event_type=event_type,
        event_no=event_no, **kws)
    return record
