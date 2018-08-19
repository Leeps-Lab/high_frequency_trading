from ..utility import nanoseconds_since_midnight as labtime
import os
from datetime import datetime

author = "hasan ali demirci"

"""
these will format logs as strings
this module will change frequently
"""


def base_row(**kwargs):
    base_row = dict()
    # converting to milliseconds for readability
    base_row['time'] = int(labtime() / 1e6)
    base_row['group'] = kwargs.get('gid', '00')
    base_row['event'] = ''
    base_row['player'] = '00'
    base_row['context'] = ''
    return base_row


def exchange(**kwargs):
    row = base_row(**kwargs)
    row['event'] = 'matching engine'
    row['context'] = kwargs['context']
    return row


def group_delay(**kwargs):
    row = base_row(**kwargs)
    row['event'] = 'delay'
    row['context'] = kwargs['dur']
    return row

def inv_trans(**kwargs):
    row = base_row(**kwargs)
    row['event'] = 'transaction'
    row['player'] = '@'
    row['context'] = 'investor transacted.'
    return row

def jump(**kwargs):
    row = base_row(**kwargs)
    row['event'] = 'jump'
    new_price = kwargs['np']  
    row['context'] = 'new price: {} !'.format(new_price)
    return row

def move_order(**kwargs):
    row = base_row(**kwargs)
    row['event'] = 'jump response order'
    speed, order = kwargs['speed'], kwargs['move_order']
    row['context'] = 'speed:{} players move order: {}'.format(speed, order) 
    return row

def player_moves(player, **kwargs):
    row = base_row(**kwargs)
    row['event'] = 'jump'
    row['player'] = kwargs['pid']
    speed = kwargs['speed']  
    role = kwargs['state']
    row['context'] = '{} {} moves.'.format(speed, role)
    return row

def no_players(speed, **kwargs):
    row = base_row(**kwargs)
    row['event'] = 'jump'
    row['context'] = 'no {} players.'.format(speed) 
    return row

def order_head(**kwargs):
    row = base_row(**kwargs)
    row['player'] = kwargs['pid']
    row['event'] = 'find most recent replace'
    row['context'] = kwargs['context'] 
    return row


def not_found(**kwargs):
    row = base_row(**kwargs)
    row['player'] = kwargs['pid']
    row['event'] = 'order not found'
    token = kwargs['token']
    row['context'] = """the order {} was not found in active orders,
                        it should be inactive already. """.format(token)
    return row


def stage_enter(**kwargs):
    row = base_row(**kwargs)
    row['event'] = 'stage enter'
    row['player'] = kwargs['pid']
    row['context'] = {
        'state': kwargs['state'],
        'speed': kwargs['speed'],
        'order': kwargs['order'],
    }
    return row
                    

def format_senter(row):
    state = row['context']['state']
    speed = row['context']['speed']
    order = row['context']['order']
    ctx = 'player {}:{}: stage: enter {}. {}'.format(state, speed, order.side, order)
    out = row
    out['context'] = ctx
    return out

def stage_replace(**kwargs):
    row = base_row(**kwargs)
    row['event'] = 'stage replace'
    row['player'] = kwargs['pid']
    row['context'] = {
        'state': kwargs['state'],
        'speed': kwargs['speed'],
        'root': kwargs.get('root', 'none'),
        'head': kwargs['head'],
        'new_order': kwargs['new']
    }
    return row

def format_sreplace(row):
    state = row['context']['state']
    speed = row['context']['speed']
    o_to_repl = row['context']['head']
    new_o = row['context']['new_order']
    root = row['context']['root']
    ctx = 'player {}:{}: stage: replace: {} -> {}:{}'.format(
        state, speed, new_o, o_to_repl, root)   
    out = row
    out['context'] = ctx
    return out

def stage_cancel(**kwargs):
    row = base_row(**kwargs)
    row['event'] = 'stage cancel'
    row['player'] = kwargs['pid']
    row['context'] = {
        'state': kwargs['state'],
        'speed': kwargs['speed'],
        'root': kwargs.get('root'),
        'head': kwargs['head'],
    }
    return row

def format_scancel(row):
    state = row['context']['state']
    speed = row['context']['speed']
    head = row['context']['head']
    ctx = 'player {}:{}: stage: cancel: {}'.format(state, speed, head)
    root = row['context']['root']
    if root:
        ctx.join('& ' + str(root))
    out = row
    out['context'] = ctx
    return out
    
def order_count(**kwargs):
    row = base_row(**kwargs)
    row['event'] = 'live orders count'
    row['player'] = kwargs['pid']
    act_count = kwargs['act_count']
    s_count = kwargs.get('stg_count', 0)
    row['context'] = 'orders count: < active:{}|staged:{} >'.format(act_count, s_count)
    return row

def orders(**kwargs):
    row = base_row(**kwargs)
    row['event'] = 'orders in market'
    row['player'] = kwargs['pid']
    row['context'] = {
        'orders':kwargs['orders']
    }
    return row

def format_orders(row):
    out = row
    orders = row['context']['orders']
    out['context'] = 'orders: {}'.format(orders)
    return out

def state_update(**kwargs):
    row = base_row(**kwargs)
    row['event'] = 'role change'
    row['player'] = kwargs['pid']
    row['context'] = 'done updating role to {}'.format(kwargs['state'])
    return row

def spread_update(**kwargs):
    row = base_row(**kwargs)
    row['event'] = 'spread change'
    row['player'] = kwargs['pid']
    row['context'] = 'updating spread to {}'.format(kwargs['spread'])
    return row

def speed_update(**kwargs):
    row = base_row(**kwargs)
    row['event'] = 'speed change'
    row['player'] = kwargs['pid']
    row['context'] = 'updating speed to {}'.format(kwargs['speed'])
    return row    

def confirm_enter(**kwargs):
    row = base_row(**kwargs)
    row['event'] = 'confirm enter'   
    row['player'] = kwargs['pid']
    row['context'] = {
        'order': kwargs['order']
    }
    return row

def format_center(row):
    out = row
    order = row['context']['order']
    out['context'] = 'confirm: enter: {}: {}'.format(order.token, order)
    return out

def confirm_replace(**kwargs):
    row = base_row(**kwargs)
    row['event'] = 'confirm replace'
    row['player'] = kwargs['pid']
    row['context'] = {
        'replaced': kwargs['replaced'],
        'replacing': kwargs['replacing'],
    }
    return row

def format_creplace(row):
    out = row
    old_o = row['context']['replaced']
    new_o = row['context']['replacing']
    out['context'] = 'confirm: replace: {} with {}. {}->{}.'.format(
        old_o.token, new_o.token, new_o, old_o
    )
    return out

def confirm_cancel(**kwargs):
    row = base_row(**kwargs)
    row['event'] = 'confirm cancel'
    row['player'] = kwargs['pid']
    row['context'] = {
        'order': kwargs['order']
    }
    return row

def format_ccancel(row):
    out = row
    order = row['context']['order']
    out['context'] = 'confirm: cancel: {}.'.format(order)
    return out

def confirm_exec(**kwargs):
    row = base_row(**kwargs)
    row['event'] = 'confirm execution'
    row['player'] = kwargs['pid']
    row['context'] = {
        'order': kwargs['order']
    }
    return row

def format_cexec(row):
    out = row
    order = row['context']['order']
    out['context'] = 'confirm: execution: {}.'.format(order)
    return out


def profit(**kwargs):
    row = base_row(**kwargs)
    row['event'] = 'profit'
    row['player'] = kwargs['pid']
    amount = kwargs['amount']
    profit = kwargs['profit']
    side = kwargs['side']
    fp = kwargs['fp']
    price = kwargs['p']
    row['context'] = 'make profit {}. <fp:{}|price:{}|side:{}> <running profit: {}>'.format(
        amount, fp, price, side, profit)
    return row
    
def cost(**kwargs):
    row = base_row(**kwargs)
    row['event'] = 'cost'
    row['player'] = kwargs['pid']
    cost = kwargs['cost']
    delta = kwargs['delta']
    unit_cost = kwargs['nanocost']
    row['context'] = 'take cost {:.2}. <delta:{}|unitcost:{:.2}>'.format(cost, delta, unit_cost)
    return row

def no_orders(**kwargs):
    row = base_row(**kwargs)
    row['event'] = 'leave market'
    row['player'] = kwargs['pid']
    row['context'] = 'no active/staged orders'
    return row