from django.core.cache import cache
import time
import logging

log = logging.getLogger(__name__)

def atomic(func):
    sleeps = []
    sleep_len = 0.001
    def atomize(self, *args, **kwargs):
        lock_key = str(self.id) + 'lock'
        c = 0 
        while cache.delete(lock_key) == 0:
            time.sleep(sleep_len)
            c += sleep_len
            continue
        log.info('%s locked %s, blocked for %f seconds.' % (func.__name__, lock_key, c))
        t = time.time()
        msgs = func(self, *args, **kwargs)
        cache.set(lock_key, 'off', timeout=None)
        diff = time.time() - t
        log.info('%s released lock: %s.' % (func.__name__, diff))
        return msgs
    return atomize
