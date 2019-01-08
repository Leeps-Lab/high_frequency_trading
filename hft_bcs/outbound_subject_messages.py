from channels import Group as CGroup, Channel
import logging
import json
from collections import namedtuple

log = logging.getLogger(__name__)


message_schemas = {
    'bbo': ('type', 'market_id', 'best_bid', 'best_offer'),
    'confirmed': ('type', 'player_id', 'order_token', 'price'),
    'replaced': ('type', 'player_id',  'price', 'order_token', 'old_token',
        'old_price'),
    'canceled': ('type', 'player_id', 'order_token', 'price'),
    'executed': ('type', 'player_id', 'order_token', 'price'),
    'system_event': ('type','market_id', 'code')
}


def broadcast(message_type, message_schemas=message_schemas, **kwargs):
    """
    broadcast via channel layer
    """
    event_fields = message_schemas.get(message_type)
    if event_fields is None:
        raise Exception('unknown broadcast event: %s in message %s' % (message_type, kwargs))
    message = {}
    message['type'] = message_type
    for key in event_fields:
        value = kwargs.get(key)
        if value is None:
            raise ValueError('key: %s is none in broadcast message: %s' % (key, kwargs))
        message[key] = value
    message = json.dumps(message)
    market_id = kwargs.get('market_id')
    if market_id is None:
        raise ValueError('market id is None: %s' % kwargs)
    channel_group = CGroup(str(market_id))
    channel_group.send({"text": message}) 