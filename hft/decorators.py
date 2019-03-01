from django.core.cache import cache
import time
import logging
import json 
from .equations import price_grid

log = logging.getLogger(__name__)

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


def timer(func):
    def timed(self, *args, **kwargs):
        t = time.time()
        res = func(self, *args, **kwargs)
        ms_diff = (time.time() - t) * 1e3
        log.info('timed function: %s: %f ms.' % (func.__name__, ms_diff))
        return res
    return timed

