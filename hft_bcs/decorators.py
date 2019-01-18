from django.core.cache import cache
import time
import logging
import itertools
import json 
from .equations import price_grid

log = logging.getLogger(__name__)

def timer(func):
    def timed(self, *args, **kwargs):
        t = time.time()
        res = func(self, *args, **kwargs)
        ms_diff = (time.time() - t) * 1e3
        log.info('timed function: %s: %f ms.' % (func.__name__, ms_diff))
        return res
    return timed

bcs_field_types = {
    str: ['side', 'type'],
    int: ['price']
}

def inbound_ws_message_preprocess(func, types=bcs_field_types):
    def clean(value, field_cls):
        clean_value = value
        if not isinstance(value, field_cls):
            clean_value = field_cls(value)
        return clean_value
    def checker(cls, raw_message, types=bcs_field_types, **kwargs):
        message = json.loads(raw_message.content['text'])
        for expected_type, expected_fields in types.items():
            for field in expected_fields:
                if field in message:
                    message[field] = clean(message[field], expected_type)
        if 'state' in message:
            message['state'] = message['state'].lower()
        if 'price' in message:
            message['price'] = price_grid(message['price'])
        out = func(cls, message, **kwargs)
        return out
    return checker



lock_name = 'trade_session_lock'
def atomic(func):
    sleep_len = 0.00125
    def atomize(*args, **kwargs):
        c = 0
        printed = False
        while cache.delete(lock_name) == 0:
            time.sleep(sleep_len)
            c += sleep_len
            if c and printed is False:
                log.info('{} waiting for the lock.'.format(func.__name__))
                printed = True
            continue
        out = func(*args, **kwargs)
        cache.set(lock_name, 'unlocked', timeout=None)
        log.info('trade session lock released.')
        return out
    return atomize



