# see https://nasdaqtrader.com/content/technicalsupport/specifications/TradingProducts/OUCH4.2.pdf
# for referance on the OUCH 4.2 format

from .utility import *

try:
    import numpy as np
except ImportError as e:
    # room to write our own error message
    raise(e)
    exit(1)

def get_types():
    msg_types = {
        (ord('S'), 10): system_event,
        (ord('E'), 40): executed,
        (ord('C'), 28): canceled,
        (ord('U'), 80): replaced,
        (ord('A'), 66): accepted
    }
    return msg_types

defaults = {
    'shares': 1,
    'stock_sym1': 1280332576,
    'stock_sym2': 538976288,
    'display': 'Y',
    'capacity': 'P',
    'iso': 'N',
    'min_quantity': 0,
    'cross_type': 'N',
    'customer_type': 'R'
    }

# Create a system event message with supplied event
# code ['S' | 'E'] and given timestamp
def system_start(event_code, timestamp=None):
    if timestamp is None:
        timestamp = Integer_To_Unit8(Get_Time("nanoseconds"),4)

    message = np.empty(10, dtype=np.uint8)

    message[0] = np.uint8(ord('H'))          # set the System message code 
    message[9] = np.uint8(ord(event_code))   # set the system event code ['S'|'E']

    # splice in timestamp
    Splice_Into_Array(message, timestamp, 1, 8)

    return message



def replace(replace_order, order):
    message = np.empty(47, dtype=np.uint8)

    message[0] = np.uint8(ord('U'))  # set the System message code

    Splice_Into_Array(message, String_To_Unit8(replace_order.token, 14), 1,
                      14)  # Splices existing_order_token into messages[]

    Splice_Into_Array(message, String_To_Unit8(order.token, 15), 15, 14)

    # Shares
    Splice_Into_Array(message, Integer_To_Unit8(defaults['shares']), 29, 4)  # Splices shares into messages[]

    Splice_Into_Array(message, Integer_To_Unit8(order.price), 33, 4)  # Splices price into messages[]

    Splice_Into_Array(message, Integer_To_Unit8(order.time_in_force), 37, 4)  # Splices time_in_force into messages[]

    message[41] = np.uint8(ord(defaults['display']))
    message[42] = np.uint8(ord(defaults['iso']))

    Splice_Into_Array(message, Integer_To_Unit8(defaults['min_quantity']), 43, 4)  # Minimum Quantity OUCH 4.2

    return message


def enter(order):
    message = np.empty(49, dtype=np.uint8)

    message[0] = np.uint8(ord('O'))  # Set the System message code

    Splice_Into_Array(message, String_To_Unit8(order.token, 14), 1, 14)

    message[15] = np.uint8(ord(order.side))

    # Shares; default to 1 for leeps experiment
    Splice_Into_Array(message, Integer_To_Unit8(defaults['shares']), 16, 4)

    # Stock Symbol;
    # Symbol created by Kristian Lopez Vargas and Eric Aldrich
    Splice_Into_Array(message, Integer_To_Unit8(defaults['stock_sym1']), 20, 4)
    Splice_Into_Array(message, Integer_To_Unit8(defaults['stock_sym2']), 24, 4)

    Splice_Into_Array(message, Integer_To_Unit8(int(order.price)), 28, 4)

    Splice_Into_Array(message, Integer_To_Unit8(order.time_in_force), 32, 4)

    Splice_Into_Array(message, String_To_Unit8(order.firm, 4), 36, 4)

    message[40] = np.uint8(ord(defaults['display']))  # Display -> Y
    message[41] = np.uint8(ord(defaults['capacity']))  # Capacity
    message[42] = np.uint8(ord(defaults['iso']))  # Intermarket Sweep Eligibility

    Splice_Into_Array(message, Integer_To_Unit8(defaults['min_quantity']), 43, 4)  # Min Quantity

    message[47] = np.uint8(ord(defaults['cross_type']))  # Cross Type
    message[48] = np.uint8(ord(defaults['customer_type']))  # Customer Type

    return message

# =========================================
# existing_order_token : order going to be replaced [14 byte alphanumeric token]
# =========================================
def cancel(existing_order_token, shares=0):
    message = np.empty(19, dtype=np.uint8)

    message[0] = np.uint8(ord('X'))  # set the System message code

    Splice_Into_Array(message, String_To_Unit8(existing_order_token, 14), 1, 14)  # Splices existing_order_token into messages[]

    # Shares; default to 1 for leeps experiment
    Splice_Into_Array(message, Integer_To_Unit8(shares), 15, 4)
    
    return message


# =========================================
# exchange_msg : byte array message received from the exchange
# =========================================
def accepted(exchange_msg):
    accepted_message = {}

    accepted_message["type"] = chr(exchange_msg[0]) # 'U' same as replace order. keep in mind
    accepted_message["timestamp"] = Byte_Array_To_Int(exchange_msg, 1, 8)
    accepted_message["order_token"] = Byte_Array_To_String(exchange_msg, 9, 14)
    accepted_message["buy_sell"] = chr(exchange_msg[23])
    accepted_message["shares"] = Byte_Array_To_Int(exchange_msg, 24, 4)  # Should add?
    # Stock is next in order but that's hardcoded in so not sure if its worth adding
    accepted_message["price"] = Byte_Array_To_Int(exchange_msg, 36)
    accepted_message["time_in_force"] = Byte_Array_To_Int(exchange_msg, 40)
    # Hardcoded firm
    accepted_message["display"] = chr(exchange_msg[48])
    # accepted_message["order_reference_number"] = Byte_Array_To_Int(exchange_msg, 49, 8)
    # accepted_message["capacity"] = chr(exchange_msg[57])
    # accepted_message["intermarket_sweep_eligibility"] = chr(exchange_msg[58])
    # accepted_message["minimum_quantity"] = Byte_Array_To_Int(exchange_msg, 59)
    # accepted_message["cross_type"] = chr(exchange_msg[63])
    # accepted_message["order_state"] = chr(exchange_msg[64])
    # accepted_message["bbo_weight_indicator"] = chr(exchange_msg[65])

    return accepted_message

# =========================================
# exchange_msg : byte array message received from the exchange
# =========================================
def replaced(exchange_msg):
    replace_message = {}

    replace_message["type"] = chr(exchange_msg[0])
    replace_message["timestamp"] = Byte_Array_To_Int(exchange_msg,1,8)
    replace_message["order_token"] = Byte_Array_To_String(exchange_msg,9,14)
    replace_message["buy_sell"] = chr(exchange_msg[23])
    replace_message["shares"] = Byte_Array_To_Int(exchange_msg, 24, 4) # Should add?
    replace_message["stock"] = Byte_Array_To_Int(exchange_msg,28,8)                 # Stock is next in order but that's hardcoded in so not sure if its worth adding
    replace_message["price"] = Byte_Array_To_Int(exchange_msg, 36)
    replace_message["time_in_force"] = Byte_Array_To_Int(exchange_msg, 40)
    replace_message["firm"] = Byte_Array_To_Int(exchange_msg, 44)
    replace_message["display"] = chr(exchange_msg[48])
    replace_message["order_reference_number"] = Byte_Array_To_Int(exchange_msg,49,8)
    replace_message["capacity"] = chr(exchange_msg[57])
    replace_message["intermarket_sweep_eligibility"] = chr(exchange_msg[58])
    replace_message["minimum_quantity"] = Byte_Array_To_Int(exchange_msg, 59)
    replace_message["cross_type"] = chr(exchange_msg[63])
    replace_message["order_state"] = chr(exchange_msg[64])
    replace_message["previous_order_token"] = Byte_Array_To_String(exchange_msg,65,14)
    replace_message["bbo"] = chr(exchange_msg[79])
    return replace_message


# =========================================
# exchange_msg : byte array message received from the exchange
# =========================================
def canceled(exchange_msg):
    cancel_message = {}

    cancel_message["type"] = chr(exchange_msg[0])
    cancel_message["timestamp"] = Byte_Array_To_Int(exchange_msg,1,8)
    cancel_message["order_token"] = Byte_Array_To_String(exchange_msg,9,14)
    cancel_message["decrement_shares"] = Byte_Array_To_Int(exchange_msg,23)
    cancel_message["reason"] = chr(exchange_msg[27])

    return cancel_message


# =========================================
# exchange_msg : byte array message received from the exchange
# =========================================
def executed(exchange_msg):
    executed_message = {}

    executed_message["type"] = chr(exchange_msg[0])
    executed_message["timestamp"] = Byte_Array_To_Int(exchange_msg,1,8)
    executed_message["order_token"] = Byte_Array_To_String(exchange_msg,9,14)
    executed_message["executed_shares"] = Byte_Array_To_Int(exchange_msg,23)
    executed_message["price"] = Byte_Array_To_Int(exchange_msg,27)
    executed_message["liquidity_flag"] = chr(exchange_msg[31])
    executed_message["match_number"] = Byte_Array_To_Int(exchange_msg, 32, 8)

    return executed_message

# =========================================
# exchange_msg : byte array message received from the exchange
# =========================================
def system_event(exchange_msg):
    system_event_message = {}

    system_event_message["type"] = chr(exchange_msg[0])
    system_event_message["timestamp"] = Byte_Array_To_Int(exchange_msg,1,8)
    system_event_message["event_code"] = chr(exchange_msg[9])

    return  system_event_message