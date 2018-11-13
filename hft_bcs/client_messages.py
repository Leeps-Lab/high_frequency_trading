
"""
messages to communicate with
client browsers
"""

def spread_change(player_id, leg_up=None, leg_low=None, token=None):
    """
    default will 0 the spread
    """
    key = "SPRCHG"
    if not leg_up and not leg_low:
        value = {player_id: 0}
    else:
        value = {player_id: {"A": leg_up, "B": leg_low, "TOK":token}}       
    msg = {key: value}
    return msg 
    
def fp_change(new_price):
    key = "FPC"
    value = new_price
    msg = {key: value}
    return msg

def execution(player_id, token, profit, orig_price, exec_price):
    key = "EXEC"
    value = {"id": player_id, "token": token, "profit": profit, 
        "orig_price": orig_price, "exec_price": exec_price}
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
