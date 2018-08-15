from django.core.cache import cache
import time
import logging

log = logging.getLogger(__name__)

def atomic(func):
    sleep_len = 0.001
    def atomize(self, *args, **kwargs):
        lock_key = str(self.id) + 'lock'
        c = 0 
        while cache.delete(lock_key) == 0:
            time.sleep(sleep_len)
            c += sleep_len
            continue
        if c>0:
            log.info('%s blocked for %f seconds.' % (func.__name__, c))
        t = time.time()
        msgs = func(self, *args, **kwargs)
        cache.set(lock_key, 'off', timeout=None)
        diff = time.time() - t
        return msgs
    return atomize



