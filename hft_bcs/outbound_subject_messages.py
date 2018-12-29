from channels import Group as CGroup, Channel
import logging
import json
from collections import namedtuple

log = logging.getLogger(__name__)


messages = {
    'bbo': ('type', 'market_id', 'best_bid', 'best_offer'),
    'confirmed': ('type', 'player_id', 'order_token', 'price'),
    'replaced': ('type', 'player_id',  'price', 'order_token', 'replaced_token'),
    'canceled': ('type', 'player_id', 'order_token'),
    'executed': ('type', 'player_id', 'order_token', 'price'),
    'system_event': ('type','market_id', 'code')
}


def broadcast(message_type, market_id, message_schemas=messages, **kwargs):
    """
    broadcast via channel layer
    """
    event_fields = message_schemas.get(message_type)
    if event_fields is None:
        raise Exception('unknown broadcast event: %s:%s' % (message_type, kwargs))
    message = {}
    message['type'] = message_type
    for key in event_fields:
        value = kwargs.get(key)
        if value is None:
            raise ValueError('key: %s returned none in broadcast message: %s' % (key, kwargs))
        message[key] = value
    message = json.dumps(message)
    channel_group = CGroup(str(market_id))
    channel_group.send({"text": message}) 