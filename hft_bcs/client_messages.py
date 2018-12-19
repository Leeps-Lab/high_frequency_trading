
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

# Spread Graph shift message sent to client on desire to shift bounds of spread graph
# def shift(event):
#         key = "SHIFT"
#         upper_bound = desired number
#         mid_point = desired number
#         lower_bound = desired number 
#         msg = {key: {"upper_bound": upper_bound, "mid_point": mid_point, "lower_bound":lower_bound} }
#         return msg

# Order Object
# def order(event):
#     key = "ORDER"
#     price = get price of transaction 
#     order_type  = replace, enter, cancel
#     msg = {key: {"type": , "token": order_token, "price": price } }

# Execution to be shown on the spread graph 
# def execution(player_id, orig_price):
#     key = "EXEC"
#     sniper = true or false
#     value = {"id": player_id, "sniper": sniper, "price": orig_price}
#     msg = {key: value}
#     return msg