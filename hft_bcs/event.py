from collections import deque
from itertools import count
from . import translator
import json
from .decorators import inbound_ws_message_preprocess

class EventFactory:

    @staticmethod
    def get_event(message_source, message, **kwargs):
        if message_source == 'exchange':
            event = LEEPSEvent.from_exchange_message(message, **kwargs)
        elif message_source == 'websocket':
            event = LEEPSEvent.from_subject_websocket_message(message, **kwargs)
        elif message_source == 'derived_event':
            event = LEEPSEvent.from_event_message(message, **kwargs)
        else:
            raise Exception('invalid message source: %s' % message_source)
        return event

class Event:

    __slots__ = ('resulting_events', 'attachments', 'outgoing_messages', 'message', 
        'event_type', 'event_source', 'reference_no')
    translator_cls = translator.LeepsOuchTranslator
    event_id = count(0,1)

    def __init__(self, event_source, event_type, message, **kwargs):
        self.reference_no = next(self.event_id)
        self.event_source = event_source
        self.event_type = event_type
        self.message = message
        self.attachments = kwargs

        self.outgoing_messages = deque()
    
    def __str__(self):
        return """event {self.reference_no}: source:{self.event_source}, type:{self.event_type}
                trigger_message: {self.message}:attachments: {self.attachments}
                outgoing messages: {self.outgoing_messages}
        """.format(self=self)

    @classmethod   
    def from_websocket_message(cls, *args, **kwargs):
        raise NotImplementedError()

    @classmethod
    def from_exchange_message(cls, *args, **kwargs):
        raise NotImplementedError()

class LEEPSEvent(Event):

    @classmethod
    @inbound_ws_message_preprocess
    def from_subject_websocket_message(cls, message, **kwargs):
        player_id = kwargs.get('player_id')
        market_id = kwargs.get('market_id')
        event_type = message['type']
        return cls('websocket', event_type, message, player_id=player_id,
            market_id=market_id)
    
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
            return int(player_id)

        market_id = kwargs.get('market_id')

        translator_class = cls.translator_cls
        message_type, message_content = translator_class.decode(message)

        player_id = None
        if message_type not in ('S', 'Q'):
            player_id = extract_player_id(**message_content)

        return cls('exchange', message_type, message_content, player_id=player_id,
            market_id=market_id)
    
    @classmethod
    def from_event_message(cls, message, **kwargs):
        event_source = message['message_type']
        event_type = message['payload']['type']
        return cls(event_source, event_type, message['payload'])
    

            

        
        
