from protocol_message_primitives import *

class CalcProtocolFields(ProtocolFieldEnum):
    message_type = ('c', 'Message Type Specifier')
    request_id = ('7s', 'Request ID')
    binary_operator = ('c', 'Binary Op')
    trinary_operator = ('3s', 'Trinary Op')
    operand_1 = ('I', '1st Operand')
    operand_2 = ('I', '2nd Operand')
    operand_3 = ('I', '3rd Operand')
    result = ('I', 'Result of Calculation')
    error_message = ('12s', 'Description of Error')
    
class CalcProtocolHeader(NamedFieldSequence):
    __slots__ = ('message_type',)
    _protocol_fields = CalcProtocolFields
    
class CalcProtocolPayloadBase(NamedFieldSequence):
    __slots__ = ()
    _protocol_fields = CalcProtocolFields
        
class CalcProtocolMessage(ProtocolMessage):
    _HeaderCls = CalcProtocolHeader
    _PayloadBaseCls = CalcProtocolPayloadBase
    
class CalcProtocolMessageTypeSpec(MessageTypeSpec):
    _MessageCls = CalcProtocolMessage
 
LookupByHeaderBytesMixin = create_attr_lookup_mixin('LookupByHeaderBytesMixin', 'header_bytes')
#LookupByHeaderBytesMixin = LookupByAttrMixin.make_mixin('LookupByHeaderBytesMixin', 'header_bytes')                                

class CalcProtocolMessageTypes(LookupByHeaderBytesMixin, CalcProtocolMessageTypeSpec, DuplicateFreeEnum):
    BinaryOp = ({'message_type': b'B'}, ['binary_operator', 'operand_1', 'operand_2'])
    TrinaryOp = ({'message_type': b'T'}, ['trinary_operator', 'operand_1', 'operand_2', 'operand_3'])
    Success = ({'message_type': b'S'}, ['result'])
    Failure = ({'message_type': b'F'}, ['error_message'])
    