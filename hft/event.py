from collections import deque
from itertools import count
from . import translator
import json

class EventFactory:

    @staticmethod
    def get_event(message_source, message, **kwargs):
        if message_source == 'exchange':
            event = Event(message_source, message, **kwargs)
        elif message_source == 'websocket':
            event = Event(message_source, message, **kwargs)
        elif message_source == 'derived_event':
            event = Event(message_source, message, **kwargs)
        else:
            raise Exception('invalid message source: %s' % message_source)
        return event

class Event:

    __slots__ = ('subsession_id', 'market_id', 'player_id', 'resulting_events', 
        'attachments', 'outgoing_messages', 'message', 'event_type', 'event_source', 'reference_no')
    translator_cls = translator.LeepsOuchTranslator
    event_id = count(1,1)

    def __init__(self, event_source, message, **kwargs):
        print(message)
        self.reference_no = next(self.event_id)
        self.subsession_id = message.subsession_id
        self.market_id = message.market_id
        self.player_id = message.player_id
        self.event_type = message.type
        self.event_source = event_source
        self.message = message
        self.attachments = kwargs

        self.outgoing_messages = deque()
    
    def __str__(self):
        return """
                event: {self.reference_no}x{self.subsession_id}x{self.market_id} 
                source:{self.event_source} 
                player: {self.player_id}
                type:{self.event_type}
                trigger_message: {self.message} 
                attachments: {self.attachments}
                outgoing messages: {self.outgoing_messages}
        """.format(self=self)
    
    def to_kwargs(self):
        kwargs = self.message.data
        if self.attachments:
            for k, v in self.attachments.items():
                if k not in kwargs:
                    kwargs[k] = v
        return kwargs

# class LEEPSEvent(Event):

    # @classmethod
    # @inbound_ws_message_preprocess
    # def from_subject_websocket_message(cls, message, **kwargs):
    #     player_id = kwargs.get('player_id')
    #     market_id = kwargs.get('market_id')
    #     subsession_id = kwargs.get('subsession_id')
    #     event_type = message['type']
    #     return cls('websocket', event_type, message, player_id=player_id,
    #         subsession_id=subsession_id, market_id=market_id)
    
    # @classmethod
    # def from_exchange_message(cls, message, **kwargs):
    #     def extract_player_id(**kwargs):
    #         token = kwargs.get('order_token')
    #         if token is None:
    #             token = kwargs.get('replacement_order_token')
    #         # index 3 is subject ID      
    #         player_id = token[5:9]
    #         if token[3] == '@':
    #             #   way out for investor orders
    #             return 0
    #         return int(player_id)

    #     market_id = kwargs.get('market_id')
    #     subsession_id = kwargs.get('subsession_id')

    #     translator_class = cls.translator_cls
    #     message_type, message_content = translator_class.decode(message)

    #     player_id = None
    #     if message_type not in ('S', 'Q'):
    #         player_id = extract_player_id(**message_content)

    #     return cls('exchange', message_type, message_content, subsession_id=subsession_id,
    #         player_id=player_id, market_id=market_id)
    
    # @classmethod
    # def from_event_message(cls, message, **kwargs):
    #     event_source = message['message_type']
    #     event_type = message['payload']['type']
    #     session_id = message['payload']['subsession_id']
    #     return cls(event_source, event_type, message['payload'], subsession_id=session_id)
    

            

        
        
