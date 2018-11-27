from exchange_server.OuchServer.ouch_messages import OuchClientMessages, OuchServerMessages
import time
import numpy as np
import datetime
import pytz
from random import randrange

class Translator(object):
    defaults = {}
    message_type_map = {}

    @staticmethod
    def decode(msg):
        header = msg[:1]
        message_spec = OuchServerMessages.lookup_by_header_bytes(header)
        payload_size = message_spec.payload_size
        payload_bytes = msg[1: 1 + payload_size]
        body = message_spec.from_bytes(payload_bytes, header=False)
        fields = {k: v.decode('utf-8') if isinstance(v, bytes) else v for
                                                    k, v in body.iteritems()}
        msg_type = header.decode('utf-8')
        return (msg_type, fields)

    @classmethod
    def encode(cls, type_spec, **kwargs):
        # temporarily putting this here 
        assert type_spec in cls.message_type_map.keys(), '%s unknown message type' % type_spec
        message_spec = cls.message_type_map[type_spec]
        for slot in message_spec.PayloadCls.__slots__:
            value = kwargs.get(slot, None)
            # TODO: the fact that I have to do this is odd.
            if isinstance(value, str):
                value = bytes(value, 'utf8')
            if value is None:
                value = cls.defaults.get(slot, None)
            assert value is not None, 'slot %s is none' % slot
            kwargs[slot] = value
        message = message_spec(**kwargs)
        return bytes(message)

class BCSTranslator(Translator):

    defaults = {
            'shares': 1,
            'stock': b'AMAZGOOG',
            'display': b'Y',
            'capacity': b'P',
            'iso': b'N',
            'min_quantity': 0,
            'cross_type': b'N',
            'customer_type': b'R',
            'intermarket_sweep_eligibility': b'N',
            'firm': b'LEEPS',
            'minimum_quantity': 1
        }

    message_type_map = {
        'enter': OuchClientMessages.EnterOrder,
        'replace': OuchClientMessages.ReplaceOrder,
        'cancel': OuchClientMessages.CancelOrder
    }

if __name__ == '__main__':
    translator = BCSTranslator()
    kwargs = {
        'enter': {'order_token': b'SUB00000000000', 'buy_sell_indicator': b'B', 
                    'price': 10, 'time_in_force': 1},
        'replace': {'existing_order_token': b'SUB00000000000', 
                        'replacement_order_token': b'SUB00000000001', 'price': 11, 
                        'time_in_force': 1 },
        'cancel': {'order_token': b'SUB00000000000'}
    }
    for k, v in kwargs.items():
        msg = translator.encode(k, **v)
        print(msg)
