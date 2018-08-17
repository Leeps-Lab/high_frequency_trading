from exchange_server.OuchServer.ouch_messages import OuchClientMessages, OuchServerMessages
import time
import numpy as np
import datetime
import pytz
from random import randrange
from .utility import nanoseconds_since_midnight as labtime

class Translator(object):
    header_size = 1

    def decode(self, msg):
        header = msg[:1]
        message_spec = OuchServerMessages.lookup_by_header_bytes(header)
        payload_size = message_spec.payload_size
        payload_bytes = msg[1: 1 + payload_size]
        body = message_spec.from_bytes(payload_bytes, header=False)
        fields = {k: v.decode('utf-8') if isinstance(v, bytes) else v for
                                                    k, v in body.iteritems()}
        msg_type = header.decode('utf-8')
        return (msg_type, fields)

    def encode(self, req):
        return bytes(req)