from collections import deque
from itertools import count
from . import translator
import json
from .message_registry import MessageRegistry
from .broadcast_message import ELOBroadcastMessageFactory
from .internal_event_message import ELOInternalEventMessageFactory


class EventFactory:

    @staticmethod
    def get_event(message_source, message, **kwargs):
        if message_source == 'exchange':
            event = ELOEvent(message_source, message, **kwargs)
        elif message_source == 'websocket':
            event = ELOEvent(message_source, message, **kwargs)
        elif message_source == 'internal_event':
            event = ELOEvent(message_source, message, **kwargs)
        else:
            raise Exception('invalid message source: %s' % message_source)
        return event


class Event:

    __slots__ = (
        'subsession_id', 'market_id', 'player_id',
        'attachments', 'outgoing_messages', 'message', 'event_type',
        'event_source', 'reference_no', 'broadcast_msgs', 'internal_event_msgs',
        'exchange_msgs')

    translator_cls = None
    internal_event_msg_factory = None
    broadcast_msg_factory = None
    exchange_msg_factory = None
    event_id = count(1, 1)

    def __init__(self, event_source, message, **kwargs):
        self.reference_no = next(self.event_id)
        self.subsession_id = message.subsession_id
        self.market_id = message.market_id
        self.player_id = message.player_id
        self.event_type = message.type
        self.event_source = event_source
        self.message = message

        self.attachments = {}

        self.internal_event_msgs = MessageRegistry(self.internal_event_msg_factory)
        self.broadcast_msgs = MessageRegistry(self.broadcast_msg_factory)
        self.exchange_msgs = MessageRegistry(self.exchange_msg_factory)
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
{self.broadcast_msgs}

    internal event messages:
{self.internal_event_msgs}

    exchange messages:
{self.exchange_msgs}

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

    def attach(self, attachments):
        self.attachments.update(attachments)


class ELOEvent(Event):
    __slots__ = (
        'subsession_id', 'market_id', 'player_id', 'resulting_events',
        'attachments', 'outgoing_messages', 'message', 'event_type', 'event_source',
        'broadcast_msgs', 'internal_event_msgs', 'reference_no')
    translator_cls = translator.LeepsOuchTranslator
    broadcast_msg_factory = ELOBroadcastMessageFactory
    internal_event_msg_factory = ELOInternalEventMessageFactory
