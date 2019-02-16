from channels import Group as CGroup, Channel
import logging
import json
from collections import namedtuple

log = logging.getLogger(__name__)


message_schemas = {
    'bbo': {'type': str, 'market_id': int, 'best_bid':int, 'best_offer':int, 
        'volume_bid': int, 'volume_offer': int},
    'reference_price': {'type': str, 'market_id': int, 'value': int},
    'order_imbalance': {'type': str, 'market_id': int, 'value': float},
    'confirmed': {'type': str, 'player_id': int, 'order_token': str, 'price': int},
    'replaced': {'type': str, 'player_id': int,  'price': int, 'order_token': str, 
        'old_token': str, 'old_price': int},
    'canceled': {'type': str, 'player_id': int, 'order_token': str, 'price': int},
    'executed': {'type': str, 'player_id': int, 'order_token': str, 'price': int,
        'inventory': int, 'endowment': int},
    'system_event': {'type': str, 'market_id': int, 'code': str}
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
    for key, value_type in event_fields.items():
        value = kwargs.get(key)
        if value is None:
            raise ValueError('key: %s is none in broadcast message: %s' % (key, kwargs))
        elif not isinstance(value, value_type):
            value = value_type(value)
        message[key] = value
    message = json.dumps(message)
    market_id = kwargs.get('market_id')
    if market_id is None:
        raise ValueError('market id is None: %s' % kwargs)
    channel_group = CGroup(str(market_id))
    channel_group.send({"text": message}) 