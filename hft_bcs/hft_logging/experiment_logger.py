from hft_bcs.utility import nanoseconds_since_midnight
import json
from datetime import datetime


# define context dictionary for each different experiment event


def header(**kwargs):
    session_id = kwargs['session']
    groups = kwargs['groups']
    design = kwargs['design']
    spread = kwargs['initial_spread']
    out = {
        'session': session_id,
        'groups': groups,       
        'design': design,
        'spread': spread
    }
    return out

def jump(**kwargs):
    return {'fp': kwargs['fp']}

def investor(**kwargs):
    return {'side': kwargs['side']}

def start(**kwargs):
    return {}

def end(**kwargs):
    return {}

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


def profit(**kwargs):
    pid = kwargs['pid']
    profit = kwargs['profit']
    source = kwargs['source']
    stamp = kwargs['stamp']
    endowment = kwargs['endowment']
    result = {
        'player_id': pid, 'profit': profit, 'source': source, 
        'timestamp': stamp, 'endowment': endowment
    }
    return result


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
    'header': header,
    'start': start,
    'jump': jump,
    'inv': investor,
    'spread': spread,
    'state': state,
    'speed': speed,
    'enter': enter,
    'exec': execution,
    'replace': replace,
    'cancel': cancel,
    'profit': profit,
    'end': end
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
