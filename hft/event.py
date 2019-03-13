from collections import deque
from itertools import count
from . import translator
import json
from .message_registry import MessageRegistry
from .outbound_message import ELOBroadcastMessageFactory

class EventFactory:

    @staticmethod
    def get_event(message_source, message, **kwargs):
        if message_source == 'exchange':
            event = ELOEvent(message_source, message, **kwargs)
        elif message_source == 'websocket':
            event = ELOEvent(message_source, message, **kwargs)
        elif message_source == 'derived_event':
            event = ELOEvent(message_source, message, **kwargs)
        else:
            raise Exception('invalid message source: %s' % message_source)
        return event

class Event:

    __slots__ = ('subsession_id', 'market_id', 'player_id', 'resulting_events', 
        'attachments', 'outgoing_messages', 'message', 'event_type', 'event_source', 'reference_no')
    translator_cls = None
    broadcast_message_factory = None
    event_id = count(1,1)

    def __init__(self, event_source, message, **kwargs):
        self.reference_no = next(self.event_id)
        self.subsession_id = message.subsession_id
        self.market_id = message.market_id
        self.player_id = message.player_id
        self.event_type = message.type
        self.event_source = event_source
        self.message = message
        self.attachments = {}

        self.broadcast_messages = MessageRegistry(self.broadcast_message_factory)
        self.outgoing_messages = deque()
    
    def __str__(self):
        return """
    event: {self.reference_no}x{self.subsession_id}x{self.market_id}
    source: {self.event_source} 
    player: {self.player_id}
    type: {self.event_type}
    original message: 
{self.message} 

    broadcast messages: 
{self.broadcast_messages}

    attachments: 
{self.attachments}

    outgoing messages: 
{self.outgoing_messages}

        """.format(self=self)
    
    def to_kwargs(self):
        kwargs = self.message.data
        for attr in ('event_source', 'reference_no'):
            kwargs[attr] = getattr(self, attr)
        if self.attachments:
            for k, v in self.attachments.items():
                if k not in kwargs:
                    kwargs[k] = v
        return kwargs


class ELOEvent(Event):
    __slots__ = ('subsession_id', 'market_id', 'player_id', 'resulting_events', 
        'attachments', 'outgoing_messages', 'message', 'event_type', 'event_source', 
        'broadcast_messages', 'reference_no')
    translator_cls = translator.LeepsOuchTranslator   
    broadcast_message_factory = ELOBroadcastMessageFactory

        
        
