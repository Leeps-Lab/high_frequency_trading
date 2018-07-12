import sys
from collections import OrderedDict
import logging as log
from exchange.order_books.book_price_q import BookPriceQ
from exchange.order_books.list_elements import SortedIndexedDefaultList

MIN_BID = 0
MAX_ASK = 2147483647

class CDABook:
	def __init__(self):
		self.bid = MIN_BID
		self.ask = MAX_ASK
		self.bids = SortedIndexedDefaultList(index_func = lambda bq: bq.price, 
							initializer = lambda p: BookPriceQ(p),
							index_multiplier = -1)
		self.asks = SortedIndexedDefaultList(index_func = lambda bq: bq.price, 
							initializer = lambda p: BookPriceQ(p))	
	def __str__(self):
		return """  Spread: {} - {}
  Bids:
{}

  Asks:
{}""".format(self.bid, self.ask, self.bids, self.asks)

	def reset_book(self):						#jason
		log.info('Clearing All Entries from Order Book')
		self.bid = MIN_BID
		self.ask = MAX_ASK
		for id in list(self.asks.index):		#force as list because can't interate dict and delete keys at same time
                	self.asks.remove(id)
		for id in list(self.bids.index):
                	self.bids.remove(id)


	def cancel_order(self, id, price, volume, buy_sell_indicator):
		'''
		Cancel all or part of an order. Volume refers to the desired remaining shares to be executed: if it is 0, the order is
		fully cancelled, otherwise an order of volume volume remains.
		'''
		orders = self.bids if buy_sell_indicator == b'B' else self.asks
		
		if price not in orders or id not in orders[price].order_q:
			log.debug('No order in the book to cancel, cancel ignored.')
			return []
		else:
			amount_canceled=0
			current_volume=orders[price].order_q[id]
			if volume==0: 										#fully cancel
				orders[price].cancel_order(id)
				amount_canceled = current_volume
				if orders[price].interest == 0:
					orders.remove(price)
			elif current_volume >= volume:
				orders[price].reduce_order(id, volume)		
				amount_canceled = current_volume - volume
			else:
				amount_canceled = 0

			if price == self.bid:
				self.update_bid()
			elif price == self.ask:
				self.update_ask()

			return [(id, amount_canceled)]
			

	def update_bid(self):
		if self.bids.start is None:
			self.bid = MIN_BID 
		else:
			self.bid = self.bids.start.data.price
		#while self.price_q[self.bid].interest == 0 and self.bid > self.min_price:
		#	self.bid -= self.decrement

	def update_ask(self):
		if self.asks.start is None:
			self.ask = MAX_ASK
		else:
			self.ask = self.asks.start.data.price
		#while self.price_q[self.ask].interest == 0 and self.ask < self.max_price:
		#	self.ask += self.decrement		

	def enter_buy(self, id, price, volume, enter_into_book):
		'''
		Enter a limit order to buy at price price: first, try and fulfill as much as possible, then enter a
		'''
		order_crosses=[]
		entered_order = None
		volume_to_fill = volume
		if price >= self.ask:
			for price_q in self.asks.ascending_items():
				if price_q.price > price:
					break
				
				(filled, fulfilling_orders) = price_q.fill_order(volume_to_fill)
				for (fulfilling_order_id, cross_volume) in fulfilling_orders:
					order_crosses.append(((id, fulfilling_order_id), price_q.price, cross_volume))
					volume_to_fill -= cross_volume
				
				if price_q.interest==0:
					self.asks.remove(price_q.price)
					self.update_ask()

				if volume_to_fill <= 0:
					break					


		if volume_to_fill > 0 and enter_into_book:
			self.bids[price].add_order(id, volume_to_fill)
			self.update_bid()
			entered_order = (id, price, volume_to_fill)
		return (order_crosses, entered_order) 

	def enter_sell(self, id, price, volume, enter_into_book):
		'''
		Enter a limit order to sell at price price: first try and fulfill as much as possible, then enter the
		remaining as a limit sell
		'''
		order_crosses=[]
		entered_order = None
		volume_to_fill = volume
		if price <= self.bid:
			for price_q in self.bids.ascending_items():
				if price_q.price < price:
					break
				
				(filled, fulfilling_orders) = price_q.fill_order(volume_to_fill)
				for (fulfilling_order_id, cross_volume) in fulfilling_orders:
					order_crosses.append(((id, fulfilling_order_id), price_q.price, cross_volume))
					volume_to_fill -= cross_volume
				
				if price_q.interest==0:
					self.bids.remove(price_q.price)
					self.update_bid()

				if volume_to_fill <= 0:
					break					
			
		if volume_to_fill > 0 and enter_into_book:
			self.asks[price].add_order(id, volume_to_fill)
			self.update_ask()
			entered_order = (id, price, volume_to_fill)
		return (order_crosses, entered_order) 

def test():
	book = CDABook()
	(crossed_orders, entered_order) =  book.enter_buy(1, 10, 2, enter_into_book = True)
	print(crossed_orders, entered_order)
	assert len(crossed_orders)==0
	assert entered_order==(1,10,2)
	assert book.bid==10

	print(book)

	(crossed_orders, entered_order)  = book.enter_buy(2, 11, 3, enter_into_book = True)
	print(crossed_orders, entered_order)
	assert len(crossed_orders)==0
	assert entered_order==(2,11,3)
	assert book.bid==11

	print(book)

	(crossed_orders, entered_order) = book.enter_sell(3, 8, 10, enter_into_book = True)
	print(crossed_orders, entered_order)
	assert len(crossed_orders)==2
	assert crossed_orders[0]==((3, 2), 11, 3)
	assert crossed_orders[1]==((3, 1), 10, 2)
	assert entered_order==(3,8,5)
	assert book.ask==8

	print(book)

	stuff = book.cancel_order(3, 8, 4, b'S')
	assert book.ask==8
	print(book)

	stuff = book.cancel_order(3, 8, 0, b'S')
	print(book)

	assert book.ask==MAX_ASK

	

	#should sell to both of the entered buy orders

if __name__ == '__main__':
	test()

