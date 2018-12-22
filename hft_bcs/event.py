


from collections import deque
from itertools import count
from . import translator
import json


class EventFactory:

   @staticmethod
    def get_event(message_source, message, **kwargs):
        if message_source == 'exchange':
            event = Event.from_exchange_message(message, **kwargs)
        elif message_source == 'websocket':
            event = Event.from_websocket_message(message, **kwargs)
        return event

class Event:

    __slots__ = ('resulting_events', 'attachments', 'outgoing_messages', 'message', 
        'event_type', 'event_topic', 'reference_no')
    translator_cls = translator.LEEPSOuchTranslator
    event_id = count(0,1)

    def __init__(self, event_source, message, **kwargs):
        self.reference_no = next(self.event_id)
        self.event_source = event_source
        self.event_type = None
        self.message = message
        self.attachments = kwargs

        self.outgoing_messages = deque()

    @classmethod   
    def from_websocket_message(cls, *args, **kwargs):
        raise NotImplementedError()

    @classmethod
    def from_exchange_message(cls, *args, **kwargs):
        raise NotImplementedError()

class LEEPSEvent(Event):

    @classmethod
    def from_websocket_message(cls, message, **kwargs):
        player_id = kwargs.get('player_id')
        group_id = kwargs.get('group_id')
        message_content = json.loads(message.content['text'])
        event_type = message_content['type']
        return cls('websocket', event_type, message_content, player_id=player_id,
            group_id=group_id)
    
    @classmethod
    def from_exchange_message(cls, message, **kwargs):
        def extract_player_id(**kwargs):
            token = kwargs.get('order_token')
            if token is None:
                token = kwargs.get('replacement_order_token')
            # index 3 is subject ID      
            player_id = token[5:9]
            if token[3] == '@':
                #   way out for investor orders
                return False
            return player_id
            
        market_id = kwargs.get('market_id')

        translator_class = cls.translator_cls
        message_type, message_content = translator_class.decode(message)

        player_id = None
        if message_type != 'S':
            player_id = extract_player_id(**message_content)

        return cls('exchange', message_type, message_content, player_id=player_id,
            market_id=market_id)

    

            

        
        
