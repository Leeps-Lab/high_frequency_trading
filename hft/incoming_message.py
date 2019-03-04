from .translator import LeepsOuchTranslator
from .equations import price_grid
from .utility import elo_scaler
import json
import logging
from .cache import get_market_id_map

log = logging.getLogger(__name__)

class IncomingMessageFactory:

    @staticmethod
    def get_message(message_source, message, **kwargs):
        if message_source == 'exchange':
            return IncomingOuchMessage(message, **kwargs)
        elif message_source == 'websocket':
            return IncomingWSMessage(message, **kwargs)
        elif message_source == 'derived_event':
            return DerivedEventMessage(message, **kwargs)
        else:
            raise Exception('invalid message source: %s' % message_source)

class IncomingMessage:

    required_fields = ('subsession_id', 'market_id', 'player_id', 'type')
    defaults = {'player_id': None}

    def __init__(self, message, **kwargs):
        self.kwargs = kwargs
        self.data = message

    @property
    def data(self):
        return self.__data
    
    @data.setter
    def data(self, message):
        incoming_message = message
        if not isinstance(message, dict):
            try:
                incoming_message = self.translate(message)
            except AttributeError:
                raise Exception('translator class must be set for non dictionary'
                    'messages')
        incoming_message = self.sanitize(incoming_message)
        for key in self.required_fields:
            if key not in incoming_message:
                try:
                    incoming_message[key] = self.kwargs[key]
                except KeyError:
                    try:
                        incoming_message[key] = self.defaults[key]
                    except KeyError:
                        raise Exception('required key %s is missing in message %s' % (
                            key, incoming_message
                        ))
        self.__data = incoming_message
        return message

    def __getattr__(self, attr_name):
        if attr_name in self.data:
            return self.data[attr_name]
        else:
            raise AttributeError('key %s is not in message %s' % (attr_name, self))

    def __str__(self):
        class_name = '%s:  ' % self.__class__.__name__ 
        content = ' '.join('{}:{}'.format(k, v) for k, v in self.data.items())
        return  class_name + content 

    def translate(self, message):
        return message
    
    def sanitize(self, message):
        return message


class IncomingWSMessage(IncomingMessage):


    def translate(self, message):
        translated_message = json.loads(message.content['text'])
        return translated_message
    
    def sanitize(self, message, scaler=elo_scaler):
        clean_message = message
        if 'market_id_in_subsession' in clean_message:
            try:
                mapping = get_market_id_map(self.kwargs['subsession_id'])
                market_id = mapping[clean_message['market_id_in_subsession']]
            except Exception as e:
                log.exception('unable to retrieve market id map from cache.')
                raise
            clean_message['market_id'] = market_id
        if self.kwargs['player_id'] != 0:
            clean_message = scaler(clean_message, direction='scale-up')
        if 'price' in clean_message:
            clean_message['price'] = price_grid(clean_message['price'])
        if 'state' in clean_message:
            clean_message['state'] = clean_message['state'].lower()
        if 'market_id' in clean_message:
            clean_message['market_id'] = str(clean_message['market_id'])
        if 'time_in_force' in clean_message:
            clean_message['time_in_force'] = int(clean_message['time_in_force'])
        return clean_message
    


class IncomingOuchMessage(IncomingMessage):


    def translate(self, message):
        translated_message = LeepsOuchTranslator.decode(message)
        return translated_message

    def sanitize(self, message):
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
            clean_message['player_id'] = player_id
        return clean_message

class DerivedEventMessage(IncomingMessage):

    def sanitize(self, message):
        clean_message = message['payload']
        return clean_message



    
