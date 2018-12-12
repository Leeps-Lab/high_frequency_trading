from django.core.cache import cache
import time
import logging
import itertools

from .hft_logging.session_events import log_events
from .hft_logging import row_formatters as hfl

log = logging.getLogger(__name__)

# TODO: fix this. circular reference being a problem. use partial maybe ?



def timer(func):
    def timed(self, *args, **kwargs):
        t = time.time()
        res = func(self, *args, **kwargs)
        diff = (time.time() - t) * 1e3
        print(diff)
        return res
    return timed

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
                log.info('{} another thread has the lock.'.format(func.__name__))
                printed = True
            continue
        out = func(*args, **kwargs)
        cache.set(lock_name, 'unlocked', timeout=None)
        return out
    return atomize



