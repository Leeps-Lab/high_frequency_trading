import struct
import logging as log

calc_field_specs = {
    'request_id': '7s',
    'binary_operator': 'c',
    'trinary_operator': '3s',
    'operand_1': 'I',
    'operand_2': 'I',
    'operand_3': 'I',
    'result': 'I',
    'error_message': '12s'
}

class CalcMessage(object):
    __slots__ = tuple()
    endianness = '!'  # Network byte order
    header = None
    payload_fmt = None
    payload_len = 0
    
    def __init__(self, **kwargs):
        for slot in self.__slots__:
            setattr(self, slot, kwargs[slot])
       
    def __str__(self):
        fields = ', '.join('{}={}'.format(slot, getattr(self, slot))
                           for slot in self.__slots__)
        return '{}({})'.format(self.__class__.__name__, fields)
    
calc_messages = {}

def create_calc_message(name, flag, fields):
    class CalcMessageType(CalcMessage):
        __slots__ = fields
        header = flag
        payload_fmt = (
            CalcMessage.endianness + ''.join( 
            calc_field_specs[slot] for slot in __slots__))
        payload_len = struct.calcsize(payload_fmt)

    CalcMessageType.__name__ = name
    calc_messages[flag] = CalcMessageType
    return CalcMessageType

create_calc_message('CalcMessageBinaryOp', b'B', ['binary_operator', 'operand_1', 'operand_2'])
create_calc_message('CalcMessageTrinaryOp', b'T', ['trinary_operator', 'operand_1', 'operand_2', 'operand_3'])
create_calc_message('CalcMessageSuccess', b'S', ['result'])
create_calc_message('CalcMessageFailure', b'F', ['error_message'])

def unpack_calc_message(header, payload):
    MessageClass = calc_messages[header]
    payload = dict(zip(
            MessageClass.__slots__, 
            struct.unpack(MessageClass.payload_fmt, payload)
        ))
    return MessageClass(**payload)
            
def pack_calc_message(msg):
    packed_header = msg.header
    packed_payload = struct.pack(msg.payload_fmt, *(getattr(msg, slot) for slot in msg.__slots__))
    return packed_header + packed_payload

def get_calc_message_payload_len(header):
    return calc_messages[header].payload_len

def handle_calc_request(msg):
    response = None
    if msg.header == b'B':
        log.debug('request: %d %s %d',
            msg.operand_1, msg.binary_operator.decode(), msg.operand_2)
        if msg.binary_operator == b'+':
            result = msg.operand_1 + msg.operand_2
            log.debug('result:  %d', result)
            if result > 2**32-1:
                log.debug('failed:  %d is max allowed value; overflow', 2**32-1)
                response = calc_messages[b'F'](error_message=b'overflow    ')
            else:
                log.debug('succeeded')
                response = calc_messages[b'S'](result=result)
        elif msg.binary_operator == b'-':
            result = msg.operand_1 - msg.operand_2
            log.debug('result:  %d', result)
            if result < 0:
                log.debug('failed:  0 is min allowed value; underflow')
                response = calc_messages[b'F'](error_message=b'underflow   ')
            else:
                log.debug('succeeded')
                response = calc_messages[b'S'](result=result)
        else:
            log.debug('unknown operation')
            response = calc_messages[b'F'](error_message=b'unknown op  ')
    elif msg.header == b'T':
        log.debug('request: %s(%d, %d, %d)',
            msg.trinary_operator.decode(), msg.operand_1, msg.operand_2, msg.operand_3)
        if msg.trinary_operator == b'MED':
            result = sorted((msg.operand_1, msg.operand_2, msg.operand_3))[1]
            log.debug('result:  %d', result)
            response = calc_messages[b'S'](result=result)
            log.debug('succeeded')
        elif msg.trinary_operator == b'AVG':
            result = (msg.operand_1 + msg.operand_2 + msg.operand_3)/3
            log.debug('result:  %f', result)
            if round(result) != result:
                response = calc_messages[b'F'](error_message=b'res not int ')
                log.debug('failed:  only integral values allowed')
            else:
                response = calc_messages[b'S'](result=int(result))
            log.debug('succeeded')
        else:
            log.debug('unknown operation')
            response = calc_messages[b'F'](error_message=b'unknown op  ')
    else:
        log.debug('unknown message type')
        response = calc_messages[b'F'](error_message=b'bad msg type')
    return response
