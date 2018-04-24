# see https://nasdaqtrader.com/content/technicalsupport/specifications/TradingProducts/OUCH4.2.pdf
# for referance on the OUCH 4.2 format

from .utility import *

try:
    import numpy as np
except ImportError as e:
    # room to write our own error message
    raise(e)
    exit(1)

# Create a system event message with supplied event
# code ['S' | 'E'] and given timestamp
def System_Event_Msg(event_code, timestamp=None):
    if timestamp is None:
        timestamp = Integer_To_Unit8(Get_Time("nanoseconds"),4)

    message = np.empty(10, dtype=np.uint8)

    message[0] = np.uint8(ord('S'))          # set the System message code 
    message[9] = np.uint8(ord(event_code))   # set the system event code ['S'|'E']

    # splice in timestamp
    Splice_Into_Array(message, timestamp, 1, 8)

    return message


# =========================================
# existing_order_token : order going to be replaced [14 byte alphanumeric token]
# subj_id              : subject id [1 byte long alpha] 
# buy_sell             : replacing a bid or ask ["UBUY" | "USELL"]
# order_id             : subject unique order id [9 byte integer]
# price                : representation of new price [4 byte unsigned integer]
# time_in_force        : time to let order live [4 byte integer]
# =========================================
def Replace_Order_Msg(existing_order_token, subj_id, buy_sell, order_id, price, time_in_force):

    message = np.empty(47, dtype=np.uint8)
  
    message[0] = np.uint8(ord('U'))    # set the System message code

    Splice_Into_Array(message, String_To_Unit8(existing_order_token, 14), 1, 14)     # Splices existing_order_token into messages[]

    message[15] = np.uint8(ord('S'))
    message[16] = np.uint8(ord('U'))
    message[17] = np.uint8(ord('B'))

    message[18] = np.uint8(ord(subj_id))

    if buy_sell == "UBUY":
        message[19] = np.uint8(ord('B'))
    elif buy_sell == "USELL":
        message[19] = np.uint8(ord('S'))
    else:
        raise Exception("Incorrect buy_sell string.")

    Splice_Into_Array(message, Integer_To_Unit8(order_id, 9), 20, 9)   # Splices order_token_id into messages[]

    # Shares
    Splice_Into_Array(message, Integer_To_Unit8(1), 29, 4)     # Splices shares into messages[]

    Splice_Into_Array(message, Integer_To_Unit8(price), 33, 4)  # Splices price into messages[]

    Splice_Into_Array(message, Integer_To_Unit8(time_in_force), 37, 4)  # Splices time_in_force into messages[]

    message[41] = np.uint8(ord('Y'))
    message[42] = np.uint8(ord('N'))

    Splice_Into_Array(message, Integer_To_Unit8(1), 43, 4)  # Minimum Quantity OUCH 4.2

    return message

# =========================================
# subj_id              : subject id [1 byte long alpha] 
# buy_sell             : replacing a bid or ask ["EBUY" | "ESELL"]
# order_id             : subject unique order id [9 byte integer]
# price                : representation of new price [4 byte unsigned integer]
# time_in_force        : time to let order live [4 byte integer]
# =========================================
def Enter_Order_Msg(subj_id, buy_sell, order_id, price, time_in_force):

    message = np.empty(49, dtype=np.uint8)

    message[0] = np.uint8(ord('O'))        # Set the System message code

    message[1] = np.uint8(ord('S'))
    message[2] = np.uint8(ord('U'))
    message[3] = np.uint8(ord('B'))
    
    message[4] = np.uint8(ord(subj_id))
    
    if(buy_sell=="EBUY"):
        message[5] = np.uint8(ord('B'))
        message[15] = np.uint8(ord('B'))
    elif(buy_sell=="ESELL"):
        message[5] = np.uint8(ord('S'))
        message[15] = np.uint8(ord('S'))

    else:
        raise Exception("Incorrect buy_sell string.")

    Splice_Into_Array(message,String_To_Unit8(str(order_id), 9), 6, 9)

    # Shares; default to 1 for leeps experiment
    Splice_Into_Array(message, Integer_To_Unit8(1), 16, 4)       

    # Stock Symbol; 
    # Symbol created by Kristian Lopez Vargas and Eric Aldrich 
    Splice_Into_Array(message, Integer_To_Unit8(1280332576), 20, 4)
    Splice_Into_Array(message, Integer_To_Unit8(538976288), 24, 4)

    Splice_Into_Array(message,Integer_To_Unit8(price), 28, 4)

    Splice_Into_Array(message,Integer_To_Unit8(time_in_force), 32, 4)
 
    message[36] = np.uint8(ord('S'))
    message[37] = np.uint8(ord('U'))
    message[38] = np.uint8(ord('B'))
    message[39] = np.uint8(ord(subj_id))

    message[40] = np.uint8(ord('Y'))   # Display -> Y
    message[41] = np.uint8(ord('P'))   # Capacity
    message[42] = np.uint8(ord('N'))   # Intermarket Sweep Eligibility

    Splice_Into_Array(message,Integer_To_Unit8(0), 43, 4)  # Min Quantity

    message[47] = np.uint8(ord('N'))   # Cross Type
    message[48] = np.uint8(ord('R'))   # Customer Type

    return message


# =========================================
# existing_order_token : order going to be replaced [14 byte alphanumeric token]
# =========================================
def Cancel_Order_Msg(existing_order_token):
    message = np.empty(19, dtype=np.uint8)

    message[0] = np.uint8(ord('X'))  # set the System message code

    Splice_Into_Array(message, String_To_Unit8(existing_order_token, 14), 1, 14)  # Splices existing_order_token into messages[]

    # Shares; default to 1 for leeps experiment
    Splice_Into_Array(message, Integer_To_Unit8(1), 15, 4)  
    
    return message
