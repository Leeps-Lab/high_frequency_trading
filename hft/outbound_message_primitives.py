from itertools import count
import json
import logging
from .translator import LeepsOuchTranslator
from .utility import elo_scaler

log = logging.getLogger(__name__)

class OutboundMessage:

    required_fields = ()
    type_field_name = 'type'
    message_count = count(1,1)

    def __init__(self, message_data:dict):
        self.reference_no = next(self.message_count)    
        self.data = message_data  

    @classmethod
    def create(cls, message_type, model=None, **kwargs):
        message_data = dict(kwargs)
        for key in cls.required_fields:
            if model:
                if hasattr(model, key):
                    message_data[key] = getattr(model, key)
            if key not in message_data:
                raise Exception('key %s is not in message %s' % (key, kwargs))
        message_data[cls.type_field_name] = str(message_type)
        try:
            message_data = cls.clean(message_data)
        except Exception as e:
            log.exception('invalid message %s: %s' % (message_data, e))
        return cls(message_data)
    
    def __str__(self):
        class_name = '%s:  ' % self.__class__.__name__ 
        content = ' '.join('{}:{}'.format(attr, getattr(self, attr)) for attr in 
            self.required_fields)
        return  class_name + content 
    
    def __getattr__(self, attr_name):
        if attr_name in self.data:
            return self.data[attr_name]
        else:
            raise Exception('key %s is not in message %s' % (attr_name, self))

    @classmethod           
    def clean(cls, message_data):
        raise NotImplementedError()


class BroadcastWSMessage(OutboundMessage):

    required_field_types = ()

    @classmethod
    def clean(cls, message_data, scaler=elo_scaler):
        clean_message =dict(message_data)
        for ix, key in enumerate(cls.required_fields):
            fieldtype = cls.required_field_types[ix]
            clean_value = fieldtype(message_data[key])
            clean_message[key] = clean_value
        clean_message = scaler(clean_message)
        return clean_message
    
    def to_json(self): 
        return json.dumps(self.data)

class BroadcastMessageFactory:

    message_types = {}

    @classmethod
    def get_message(cls, message_type, **kwargs):
        try:
            message_class = cls.message_types[message_type]
        except KeyError:
            raise Exception('unknown message type %s for %s' % (message_type, 
                cls.__name__))
        else:
            message = message_class.create(message_type, **kwargs)
            return message

class OutboundExchangeMessage(OutboundMessage):


    #TODO: this should somehow inherit from
    # OUCHMessage, I will think about it later.
    # this should do it for now.
    translator_cls = LeepsOuchTranslator

    def clean(cls, message_data): return message_data
    
    def translate(self, message_data) -> bytes:
        return LeepsOuchTranslator.encode(message_data['type'], **message_data)

