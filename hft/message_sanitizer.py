
from .cache import get_market_id_map
from .equations import price_grid

class MessageSanitizer:
    
    @classmethod
    def sanitize(cls, message, **kwargs):
        raise NotImplementedError()


class ELOWSMessageSanitizer(MessageSanitizer):

    @classmethod
    def sanitize(cls, message, **kwargs):
        clean_message = message
        if 'market_id_in_subsession' in clean_message:
            mapping = get_market_id_map(kwargs['subsession_id'])
            market_id = mapping[clean_message['market_id_in_subsession']]
            clean_message['market_id'] = market_id
        if 'price' in clean_message:
            clean_message['price'] = price_grid(clean_message['price'])
        if 'state' in clean_message:
            clean_message['state'] = clean_message['state'].lower()
        if 'market_id' in clean_message:
            clean_message['market_id'] = int(clean_message['market_id'])
        if 'time_in_force' in clean_message:
            clean_message['time_in_force'] = int(clean_message['time_in_force'])
        if clean_message['type'] == 'investor_arrivals':
            clean_message['player_id'] = clean_message['market_id']
        if clean_message['type'] == 'slider':
            for s in ('a_x', 'a_y', 'a_z'):
                clean_message[s] = float(clean_message[s])
        return clean_message
    

class ELOOuchMessageSanitizer(MessageSanitizer):

    @classmethod
    def sanitize(cls, message, **kwargs):
        if 'player_id' not in message:
            clean_message = message
            token = clean_message.get('order_token')
            if token is None:
                token = clean_message.get('replacement_order_token')
            # index 3 is subject ID
            event_type = message['type']
            player_id = None
            if event_type not in ('S', 'Q'):      
                player_id = int(token[5:9])
                prefix = token[0:3]
                clean_message['token_prefix'] = prefix.lower()
            clean_message['player_id'] = player_id
        return clean_message


class ELOInternalEventMessageSanitizer(MessageSanitizer):

    @classmethod
    def sanitize(cls, message, **kwargs):
        return message
