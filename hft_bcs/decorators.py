from django.core.cache import cache
import time
import logging

log = logging.getLogger(__name__)


# TODO: fix this. circular reference being a problem. use partial maybe ?

key = '{self.code}_redis_lock'

def atomic(func):
    sleep_len = 0.001
    def atomize(self, *args, **kwargs):
        lock_key = key.format(self=self)
        c = 0 
        while cache.delete(lock_key) == 0:
            time.sleep(sleep_len)
            c += sleep_len
            continue
        if c>0:
            log.info('%s: %s blocked for %f seconds.' % (self.id, func.__name__, c))
        out = func(self, *args, **kwargs)
        cache.set(lock_key, 'unlocked', timeout=None)
        return out
    return atomize



