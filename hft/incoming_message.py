from .translator import LeepsOuchTranslator
from .equations import price_grid
import json
import logging
from .cache import get_market_id_map
from .message_sanitizer import (
    ELOWSMessageSanitizer, ELOOuchMessageSanitizer, ELODerivedEventMessageSanitizer)

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
    sanitizer_cls = None

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
                raise Exception('translator class must be set for protocol'
                                'messages')
        if self.sanitizer_cls is not None:
            incoming_message = self.sanitizer_cls.sanitize(
                incoming_message, **self.kwargs)
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
        return class_name + content

    def translate(self, message):
        return message


class IncomingWSMessage(IncomingMessage):

    def translate(self, message):
        translated_message = json.loads(message.content['text'])
        return translated_message


class ELOIncomingWSMessage(IncomingWSMessage):

    sanitizer_cls = ELOWSMessageSanitizer


class IncomingOuchMessage(IncomingMessage):

    def translate(self, message):
        translated_message = LeepsOuchTranslator.decode(message)
        return translated_message


class ELOIncomingOuchMessage(IncomingOuchMessage):

    sanitizer_cls = ELOOuchMessageSanitizer


class InternalEventMessage(IncomingMessage):
    
    def translate(self, message):
        kwargs = {}
        for field in message.required_fields:
            kwargs[field] = getattr(message, field)
        return kwargs

class ELOInternalEventMessage(DerivedEventMessage):
    
    sanitizer_cls = ELODerivedEventMessageSanitizer  
