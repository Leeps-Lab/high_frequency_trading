
from .cache import get_market_id_table
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
            market_id_in_subsession = clean_message['market_id_in_subsession']
            market_id = market_id_in_subsession
            if market_id_in_subsession is not 0:
                id_table = get_market_id_table(kwargs['subsession_id'])
                if not id_table:
                    raise Exception('id to id in subsession table is none.')
                market_id = id_table[market_id_in_subsession]
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
            event_type = message['type']
            player_id = None
            if event_type not in ('S', 'Q', 'Z', 'L'):
                player_id = int(token[5:9])
                clean_message['firm'] = token[0:4].lower()
            # hack: need to set player id for peg state messages so they can be added to trader id
            # just use investor id and firm
            if event_type == 'L':
                player_id = 1
                clean_message['firm'] = 'inve'
            clean_message['player_id'] = player_id
        return clean_message


class ELOInternalEventMessageSanitizer(MessageSanitizer):

    @classmethod
    def sanitize(cls, message, **kwargs):
        return message
