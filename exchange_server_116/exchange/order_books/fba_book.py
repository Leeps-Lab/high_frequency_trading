from exchange.order_books.book_price_q import BookPriceQ
from exchange.order_books.list_elements import SortedIndexedDefaultList
import heapq
import math
import logging as log

MIN_BID = 0
MAX_ASK = 2147483647

def merge(ait, bit, key):
    """
    >>> [a for a in merge(iter([1]), iter([4]), lambda i:i)]
    [1,4]
    >>> [a for a in merge(iter([4]), iter([1]), lambda i:i)]
    [1, 4]
    >>> [a for a in merge(iter([1,2,3, 10]), iter([2,4,7]), lambda i:i)]
    [1,2,2,3,4,7,10]
    """
    a=None
    b=None
    try:
        a = next(ait)
    except StopIteration:
        yield from bit
        return
    if a is not None:
        try:
            b = next(bit)
        except StopIteration:
            yield a
            yield from ait
            return

        while b is not None:
            try:
                try:
                    while(key(a) <= key(b)):
                        yield a
                        a = next(ait)
                except StopIteration:
                    yield b
                    yield from bit
                    return

                yield b
                b = next(bit)
            except StopIteration:
                yield a
                yield from ait 
                return

class FBABook:
    def __init__(self):
        self.bids = SortedIndexedDefaultList(index_func = lambda bq: bq.price, 
                            initializer = lambda p: BookPriceQ(p),
                            index_multiplier = -1)
        self.asks = SortedIndexedDefaultList(index_func = lambda bq: bq.price, 
                            initializer = lambda p: BookPriceQ(p))

    def __str__(self):
        return """
  Bids:
{}

  Asks:
{}""".format(self.bids, self.asks)

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
            if volume==0:                                       #fully cancel
                orders[price].cancel_order(id)
                amount_canceled = current_volume
                if orders[price].interest == 0:
                    orders.remove(price)
            elif volume < current_volume:
                orders[price].reduce_order(id, volume)      
                amount_canceled = current_volume - volume
            else:
                amount_canceled = 0

            return [(id, amount_canceled)]

    def enter_buy(self, id, price, volume, enter_into_book = True):
        '''
        Enter a limit order to buy at price price: do NOT try and match
        '''
        if enter_into_book:
            self.bids[price].add_order(id, volume)
            entered_order = (id, price, volume)
            return ([], entered_order)
        else:
            return ([], None)

    def enter_sell(self, id, price, volume, enter_into_book):
        '''
        Enter a limit order to sell at price price: do NOT try and match
        '''
        if enter_into_book:
            self.asks[price].add_order(id, volume)
            entered_order = (id, price, volume)
            return ([], entered_order) 
        else:
            return ([], None)

    def batch_process(self):
        log.debug('Running batch auction..')
        log.debug('order book=%s', self)
        asks_volume = sum([price_book.interest for price_book in self.asks.ascending_items()])
        log.debug('total volume offered in batch: %d', asks_volume)
        all_orders_descending = merge(
            self.asks.descending_items(),
            self.bids.ascending_items(), 
            key= lambda bpq: -bpq.price)
        log.debug('ask prices=%s:%s, \n bid prices=%s:%s', 
            [(p.price, p.interest) for p in self.asks.ascending_items()],
            [(p.price, p.interest) for p in self.asks.descending_items()], 
            [(p.price, p.interest) for p in self.bids.ascending_items()],
            [(p.price, p.interest) for p in self.bids.descending_items()])
        assert len([p.price for p in self.asks.descending_items()])==len([p.price for p in self.asks.ascending_items()]) 
        
        orders_volume = prior_orders_volume = 0
        clearing_price=None
        log.debug('calculating clearing price..')
        bpq=prior_bpq=None

        min_real_price = None
        max_real_price = None

        log.debug('all orders descending: %s', [(b.price,b.interest) for b in merge(
            self.asks.descending_items(),
            self.bids.ascending_items(), 
            key= lambda bpq: -bpq.price)])
        
        for bpq in all_orders_descending:
            #update min/max prices
            if MIN_BID<bpq.price<MAX_ASK:
                if max_real_price is None or max_real_price < bpq.price:
                    max_real_price = bpq.price
                if min_real_price is None or bpq.price<min_real_price:
                    min_real_price = bpq.price
            #process and deal with volumes
            prior_orders_volume = orders_volume
            orders_volume += bpq.interest
            log.debug('  checking price %s, vol %s/%s', bpq.price, orders_volume, asks_volume)
            if orders_volume > asks_volume:
                break
            prior_bpq=bpq

        #if bpq.price is still at MAX_ASK, loop until price is less than max_ask and use that price
        if bpq is not None and bpq.price==MAX_ASK:
            for bpq in all_orders_descending:
                if max_real_price is None or max_real_price<bpq.price<MAX_ASK:
                    max_real_price = bpq.price
                if min_real_price is None or MIN_BID<bpq.price<min_real_price:
                    min_real_price = bpq.price
                log.debug(' looping until price <%s: current price:%s', MAX_ASK, bpq.price)
                if bpq.price<MAX_ASK:
                    break

        #If prior_orders_volume exactly hit asks and loop was able to continue, price is averaged, otherwise its the first price that pushed over limit.
        if max_real_price is None and min_real_price is None:
            clearing_price = None #no real prices - can't match if all bids/offers are market orders
        elif prior_orders_volume==asks_volume and prior_bpq is not None:
            if prior_bpq.price==MAX_ASK and MIN_BID<bpq.price<MAX_ASK:
                clearing_price=bpq.price
                log.debug(' clearing price set as bpq: {} -> {}'.format(bpq.price, clearing_price))
            elif prior_bpq.price<MAX_ASK and MIN_BID<bpq.price:
                clearing_price = math.ceil((prior_bpq.price+bpq.price)/2)
                log.debug(' clearing price is the average of {} and {} -> {}'.format(prior_bpq.price, bpq.price, clearing_price))
            elif MIN_BID<prior_bpq.price<MAX_ASK and MIN_BID==bpq.price:
                clearing_price=prior_bpq.price
                log.debug(' clearing price set as prior bpq: {} -> {}'.format(prior_bpq.price, clearing_price))
            elif prior_bpq.price==MIN_BID:
                clearing_price=min_real_price
                log.debug(' clearing price set as min real price: {}'.format(clearing_price))
        elif orders_volume>asks_volume:
            clearing_price = max(bpq.price, min_real_price)
            log.debug(' clearing price set as max of bpq and min real price: {}:{} -> {}'.format(bpq.price, min_real_price, clearing_price))



        log.debug('market clears @ %s', clearing_price)

        matches = []
        ask_it = self.asks.ascending_items()
        if clearing_price is not None:
            try:
                ask_node = next(ask_it)
                ask_price = ask_node.price
                log.debug('check ask node:{}'.format(ask_node))
                #iterate over bids starting with highest
                for bid_node in self.bids.ascending_items():
                    log.debug('   check bid node:{}'.format(bid_node))
                    bid_price = bid_node.price
                    log.info('bid price {}, ask price {}, clearing price {}'.format(bid_price, ask_price, clearing_price))
                    if bid_price<clearing_price or ask_price>clearing_price:
                        log.debug('no cross at {}'.format(ask_price))
                        break
                    else:
                        for (bid_id, volume) in list(bid_node.order_q.items()):
                            volume_filled = 0
                            log.debug('      process bid {} with volume {}.'.format(bid_id, volume))
                            while volume_filled < volume and ask_price <= clearing_price:
                                (filled, fulfilling_orders) = ask_node.fill_order(volume-volume_filled)
                                volume_filled += filled
                                matches.extend([((bid_id, ask_id), clearing_price, volume) for (ask_id, volume) in fulfilling_orders])
                                log.debug('      all matching orders at node {}'.format(matches))
                                if ask_node.interest == 0:
                                    log.debug('   no more interest at ask node, removing...')
                                    self.asks.remove(ask_price) 
                                if volume_filled < volume:
                                    log.info('      bid is filled only partially {}/{}.'.format(volume_filled, volume))
                                    try: 
                                        ask_node = next(ask_it)
                                        ask_price = ask_node.price
                                    except StopIteration as e:
                                        log.debug(' stopped iteration at {}'.format(ask_price)) 
                                        break
                            #update bid in book
                            assert volume_filled<=volume
                            if volume_filled==volume:
                                log.debug('      bid {} is filled completely {}/{}.'.format(bid_id, volume_filled, volume))
                                bid_node.cancel_order(bid_id)
                                if bid_node.interest == 0:
                                    log.debug('    no more interest at bid node, removing...')
                                    self.bids.remove(bid_node.price)
                            elif volume_filled >0:
                                log.debug('     reducing {} out of {}, bid id: {}'.format(volume_filled, volume, bid_id))
                                bid_node.reduce_order(bid_id, volume - volume_filled)
            except StopIteration as e:
                log.debug(e)
                pass
        return matches



