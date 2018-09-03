from django.core.cache import cache
import time
import logging
import itertools

log = logging.getLogger(__name__)


# TODO: fix this. circular reference being a problem. use partial maybe ?

key = '{self.code}_lock'

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
                log.info('%s: key %s is locked.' % (self.id, lock_key))
                printed = True
            continue
        out = func(self, *args, **kwargs)
        cache.set(lock_key, 'unlocked', timeout=None)
        return out
    return atomize



