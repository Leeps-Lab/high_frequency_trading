from django.core.cache import cache
import time
import logging
import itertools

from .hft_logging.session_events import log_events
from .hft_logging import row_formatters as hfl

log = logging.getLogger(__name__)

author = 'hasan ali demirci'

# TODO: fix this. circular reference being a problem. use partial maybe ?

key = '{self.code}_lock'

def timer(func):
    def timed(self, *args, **kwargs):
        t = time.time()
        res = func(self, *args, **kwargs)
        diff = (time.time() - t) * 1e3
        print(diff)
        return res
    return timed



def format_output(func):
    keys = ('exchange', 'broadcast', 'order_history')
    def normalize_result(self, *args, **kwargs):
        raw_result = func(self, *args, **kwargs)
        if raw_result is None:
            result = {k: None for k in keys}
        else:
            result = raw_result
            for k in keys:
                if k not in result:
                    result[k] = None
        return result
    return normalize_result
                    

def atomic(func):
    sleep_len = 0.00125
    def atomize(self, *args, **kwargs):
        lock_key = key.format(self=self)
        c = 0
        printed = False
        while cache.delete(lock_key) == 0:
            time.sleep(sleep_len)
            c += sleep_len
            if c and printed is False:
                log.info('{}:{}:{} another thread has the lock.'.format(self, self.id, func.__name__))
                printed = True
            continue
        log_events.push(hfl.db_lock, **{'pid': self.id, 'f': func.__name__, 'state': 'locked'})    
        out = func(self, *args, **kwargs)
        cache.set(lock_key, 'unlocked', timeout=None)
        log_events.push(hfl.db_lock, **{'pid': self.id, 'f': func.__name__, 'state': 'unlocked'})  
        return out
    return atomize



