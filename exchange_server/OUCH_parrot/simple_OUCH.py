import struct


class OUCHMessage(object):
	''' Parent class for restricted class of OUCH v4.2 messages
	See ouch documentation here: http://nasdaqtrader.com/content/technicalsupport/specifications/TradingProducts/OUCH4.2.pdf'''

	buy_sell_indicator_code = { 'B': 'Buy', 'S': 'Sell' }

	def encode(self):
		return struct.pack(self.struct_format_str, *self.fields())

	@classmethod
	def from_OUCH(cls, message):
		args = struct.unpack(cls.struct_format_str, message)[1:]
		print(args)
		return cls(*args)

	def __str__(self):
		return str(self.fields())

BYTE_ORDER = '>' #big-endian

TYPE_FORMAT = 'c'
ORDER_TOKEN_FORMAT = '14s'
BUY_SELL_INDICATOR_FORMAT = 'c'
SHARES_FORMAT = 'L'
STOCK_FORMAT = '8s'
PRICE_FORMAT = 'L'
TIMESTAMP_FORMAT = 'q' ## long long, 8 bytes


##### Inbound messages

class EnterOrderOUCHMessage(OUCHMessage):
	struct_format_str = (	BYTE_ORDER + 
							TYPE_FORMAT + 
							ORDER_TOKEN_FORMAT + 
							BUY_SELL_INDICATOR_FORMAT +
							SHARES_FORMAT + 
							STOCK_FORMAT + 
							PRICE_FORMAT )

	def __init__(self, order_token, 
				buy_sell_indicator, shares, stock, price):
		self.type = b'O'  								# format c
		self.order_token = order_token					# format 14s
		self.buy_sell_indicator = buy_sell_indicator 	# format c
		self.shares = shares 							# format L, unsigned int
		self.stock = stock								# format 8s	
		self.price = price								# format L, unsigned int
	
	def fields(self):
		return (self.type, self.order_token, self.buy_sell_indicator, self.shares, 
					self.stock, self.price )

class ReplaceOrderOUCHMessage(OUCHMessage):
	struct_format_str = (	BYTE_ORDER + 
							TYPE_FORMAT + 
							ORDER_TOKEN_FORMAT + 
							ORDER_TOKEN_FORMAT + 
							SHARES_FORMAT + 
							PRICE_FORMAT )

	def __init__(self, existing_order_token, replacement_order_token, shares, price):
		self.type = b'U'											#format c
		self.existing_order_token = existing_order_token		#format 14s
		self.replacement_order_token = replacement_order_token 	#format 14s
		self.shares = shares									#format L, unsigned int
		self.price = price										#format L, unsigned int

	def fields(self):
		return (self.type, self.existing_order_token, self.replacement_order_token, 
			self.shares, self.price)

class CancelOrderOUCHMessage(OUCHMessage):
	struct_format_str = (	BYTE_ORDER + 
							TYPE_FORMAT + 
							ORDER_TOKEN_FORMAT + 
							SHARES_FORMAT )

	def __init__(self, order_token, shares):
		self.type=b'X'					#format c
		self.order_token = order_token  #format 14s
		self.shares = shares 			#formatl L, unsigned int

	def fields(self):
		return (self.type, self.order_token, self.shares)


class ModifyOrderOUCHMessage(OUCHMessage):
	struct_format_str = (	BYTE_ORDER + 
							TYPE_FORMAT + 
							ORDER_TOKEN_FORMAT +
							BUY_SELL_INDICATOR_FORMAT +  
							SHARES_FORMAT )

	def __init__(self, order_token, buy_sell_indicator, shares):
		self.type = b'M'					#format c
		self.order_token = order_token   #format 14s
		self.buy_sell_indicator = buy_sell_indicator  #format c
		self.shares = shares             #format L
	
	def fields(self):
		return (self.type, self.order_token, self.buy_sell_indicator, self.shares)


##########System event messages

class AcceptedOUCHMessage(OUCHMessage):
	struct_format_str = (	BYTE_ORDER + 
							TYPE_FORMAT + 
							TIMESTAMP_FORMAT +
							ORDER_TOKEN_FORMAT +
							BUY_SELL_INDICATOR_FORMAT +  
							SHARES_FORMAT +
							STOCK_FORMAT +
							PRICE_FORMAT)

	def __init__(self, timestamp, order_token, buy_sell_indicator, shares, stock, price):
		self.type = b'A' 							  # c
		self.timestamp = timestamp                    # L - number of nanoseconds since midnight
		self.order_token = order_token                # 14s
		self.buy_sell_indicator = buy_sell_indicator  # c
		self.shares = shares                          # L
		self.stock = stock                            # 8s
		self.price = price                            # L

	def fields(self):
		return (self.type, self.timestamp, self.order_token, self.buy_sell_indicator, self.shares, 
			self.stock, self.price)

class ReplacedOUCHMessage(OUCHMessage):
	struct_format_str = '>cL14scL8sL'

	def __init__(self, timestamp, replacement_order_token, buy_sell_indicator, shares, stock, price):
		self.type = b'U'											# c
		self.timestamp = timestamp                              #L - nanoseconds since midnight
		self.replacement_order_token = replacement_order_token  #14s
		self.buy_sell_indicator = buy_sell_indicator            #c
		self.shares = shares                                    #L
		self.stock = stock                                      #8s
		self.price = price                                      #L

	def fields(self):
		return (self.type, self.timestamp, self.replacement_order_token, self.buy_sell_indicator, 
			self.shares, self.stock, self.price)

class CanceledOUCHMessage(OUCHMessage):
	cancelled_indicator_code = {'U': 'User requested cancel', 
								'I': 'Immediate or Cancel order',
								'T': 'Timeout. The Time In Force for this order has expired',
								'S': '''Supervisory. This order was manually canceled or reduced by a NASDAQ 
								supervisory terminal. This is usually in response to a participant request via telephone.''',
								'D': '''This order cannot be executed because of a regulatory restriction 
										(e.g.: trade through restrictions).''',
								'Q': '''Self Match Prevention. The order was cancelled because it would have executed with 
										an existing order entered by the same MPID.''',
								'Z': '''System cancel. This order was cancelled by the system.''',
								'C':'''Cross cancelled. Non bookable cross orders that did not execute in the cross'''}
	struct_format_str = '>cL14sLcLL'
	def __init__(self, timestamp, order_token, decrement_shares, reason, quantity_prevented_from_trading, execution_price):
		self.type=b'D'                                                           #c
		self.timestamp=timestamp                                                #L
		self.order_token=order_token                                            #14s
		self.decrement_shares = decrement_shares                                #L
		self.reason = reason                                                    #c
		self.quantity_prevented_from_trading = quantity_prevented_from_trading  #L
		self.execution_price = execution_price                                  #L

	def fields(self):
		return (self.type, self.timestamp, self.order_token, self.decrement_shares, self.reason, 
			self.quantity_prevented_from_trading, self.execution_price)

class ExecutedOUCHMessage(OUCHMessage):
	struct_format_str = '>cL14sLLQ'

	def __init__(self, timestamp, order_token, executed_shares, execution_price, match_number):
		self.type=b'E'							#c
		self.timestamp = timestamp              #L
		self.order_token = order_token          #14s
		self.executed_shares = executed_shares  #L
		self.execution_price = execution_price  #L
		self.match_number = match_number        #Q

	def fields(self):
		return (self.type, self.timestamp, self.order_token, self.executed_shares, self.execution_price, self.match_number)


def parse_OUCH(message):
	'''Given a string in OUCH representation, returns the python object representing 
	the message'''
	message_type = chr(message[0])
	if message_type=='O':
		return EnterOrderOUCHMessage.from_OUCH(message)
	elif message_type=='U':
		return ReplaceOrderOUCHMessage.from_OUCH(message)
	elif message_type=='X':
		return CancelOrderOUCHMessage.from_OUCH(message)


if __name__ == '__main__':
	'''Sample testing use of simple OUCH messages'''
	m = EnterOrderOUCHMessage(order_token = b'00000000000000', buy_sell_indicator=b'B', shares=10, stock=b'ABC', price=15)
	encoded = m.encode()
	print("Encoded message={}".format(encoded))
	message = parse_OUCH(encoded)
	print("Decoded message={}\n{}".format(message, message.fields()))
	assert message.type == b'O'
	assert message.shares == 10
	assert message.price == 15
	assert message.stock == b'ABC\x00\x00\x00\x00\x00'