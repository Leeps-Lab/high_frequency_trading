from .utility import nanoseconds_since_midnight
import json
from datetime import datetime


# define context dictionary for each different experiment event

def jump(**kwargs):
    return {'fp': kwargs['fp'] }

def investor(**kwargs):
    return {'side': kwargs['side']}

def spread(**kwargs):
    pid = kwargs['pid']
    nspread = kwargs['nspread']
    return {'player_id': pid, 'spread': nspread}

def state(**kwargs):
    pid = kwargs['pid']
    nstatus = kwargs['nstate']
    return {'player_id': pid, 'state': nstatus} 

def speed(**kwargs):
    pid = kwargs['pid']
    nspeed = kwargs['nspeed']
    return {'player_id': pid, 'speed': nspeed}  

def enter(**kwargs):
    pid = kwargs['pid']
    token = kwargs['token']
    price = kwargs['price']
    stamp = kwargs['stamp']
    side = kwargs['side']
    tif = kwargs['tif']
    result = {
        'player_id': pid, 'order_token': token, 'price': price, 
        'timestamp': stamp, 'side': side, 'time_in_force': tif
    }
    return result

def execution(**kwargs):
    pid = kwargs['pid']
    token = kwargs['token']
    price = kwargs['price']
    stamp = kwargs['stamp']
    result = {
        'player_id': pid, 'order_token': token, 'price': price, 'timestamp': stamp
    }
    return result

def replace(**kwargs):
    pid = kwargs['pid']
    otoken = kwargs['old_token']
    ntoken = kwargs['new_token']
    stamp = kwargs['stamp']
    result = {
        'player_id': pid, 'replaced_token': otoken, 'new_token': ntoken, 
        'timestamp': stamp
    }
    return result

def cancel(**kwargs):
    pid = kwargs['pid']
    token = kwargs['token']
    stamp = kwargs['stamp']
    result = {
        'player_id': pid, 'order_token': token, 'timestamp': stamp
    }
    return result


dispatch = {
    'jump': jump,
    'inv': investor,
    'spread': spread,
    'state': state,
    'speed': speed,
    'enter': enter,
    'exec': execution,
    'replace': replace,
    'cancel': cancel
}

def prepare(**kwargs):
    time = nanoseconds_since_midnight()
    level, typ = kwargs.pop('level'), kwargs.pop('typ')
    group = kwargs.pop('group')
    result = {
        'time': time,
        'group': group,
        'level': level,
        'type': typ,
        'context': dispatch[typ](**kwargs)
    }

    return json.dumps(result)


# define custom filter to filter out non-lab logs

class custom_filter(object):
    def __init__(self):
        self.__level = 5    # lower than DEBUG

    def filter(self, logRecord):
        return logRecord.levelno == self.__level


