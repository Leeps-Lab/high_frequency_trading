from channels import Group as CGroup, Channel
import json

"""
messages to communicate with
client browsers
"""

def spread_change(id=None, leg_up=None, leg_down=None, order_token=None, **kwargs):
    """
    default will 0 the spread
    """
    key = "SPRCHG"
    if not leg_up and not leg_down:
        value = {str(id): 0}
    else:
        value = {str(id): {"A": leg_up, "B": leg_down, "TOK":order_token}}       
    msg = {key: value}
    return msg 
    
def bbo_change(best_bid=None, best_offer=None):
    pass

def fp_change(new_price=None):
    key = "FPC"
    value = new_price
    msg = {key: value}
    return msg

def execution(id=None, order_token=None, profit=None, **kwargs):
    key = "EXEC"
    value = {"id": str(id), "token": order_token, "profit": profit}
    msg = {key: value}
    return msg

def start_session():
    key = "SYNC"
    value = 0
    msg = {key: value}
    return msg

def total_role(totals_dict):
    key = "TOTAL"
    value = totals_dict
    msg = {key: value}
    return msg

def batch(event):
    key = "BATCH"
    value = event
    msg = {key: value}
    return msg

dispatch = {
    'maker_confirm': spread_change,
    'leave_market': spread_change,
    'executed': execution,
    'fundamental_price_change': fp_change,
    'batch': batch,
    'session_start': start_session,
    'bbo': bbo_change
    # 'canceled': 
}

def broadcast(message_type, group_id, **kwargs):
    """
    broadcast via channel layer
    """
    f = dispatch[message_type]
    if f is None:
        return
    msg = f(**kwargs)
    message = json.dumps(msg)
    CGroup(str(group_id)).send({"text": message}) 