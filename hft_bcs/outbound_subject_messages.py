from channels import Group as CGroup, Channel
import logging
import json

log = logging.getLogger(__name__)


messages = {
    'market': ('bbo', 'best_bid', 'best_offer'),
    'trader': ('action', 'order_token', 'price'),
    'system_event': ('type', 'content'),
}


def broadcast(message_type, group_id, **kwargs):
    """
    broadcast via channel layer
    """
    channel_group = CGroup(str(group_id))
    event_fields = messages.get(message_type)
    if event_fields is None:
        log.warning('unknown broadcast event: %s:group %s' % (message_type, group_id))
    message = {}
    for key in event_fields:
        value = kwargs.get(key)
        if value is None:
            log.warning('key %s returned none value. group id %s:message type: %s' 
                % (key, group_id, message_type))
        message[key] = value
    message = json.dumps(message)
    channel_group.send({"text": message}) 