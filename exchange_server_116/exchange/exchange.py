import sys
import asyncio
import asyncio.streams
import configargparse
import logging as log
import itertools
from functools import partial
from collections import deque

from OuchServer.ouch_messages import OuchClientMessages, OuchServerMessages
from OuchServer.ouch_server import nanoseconds_since_midnight

from exchange.order_store import OrderStore

###
# TODOs:
##  - how should status be changing in order store?
##  - how should messages be sent?
##      can we just do the current communication channel approach?
##      
##      



class Exchange:
    def __init__(self, order_book, order_reply, loop, order_book_logger = None, message_broadcast = None):
        '''
        order_book - the book!
        order_reply - post office reply function, takes in 
                message 
                original order
                context
            and does whatever we need to get that info back to order sender                             
        '''
        log.debug('Initializing exchange')
        self.order_store = OrderStore()
        self.order_book = order_book
        self.order_reply = order_reply
        self.message_broadcast = message_broadcast
        self.next_match_number = 0
        self.loop = loop
        self.outgoing_messages = deque()
        self.order_ref_numbers = itertools.count(1, 2)  # odds
        self.order_book_logger = order_book_logger
        self.start_time = 0 #jason       
        self.outgoing_broadcast_messages = deque()  # ali
        self.handlers = { 
            OuchClientMessages.EnterOrder: self.enter_order_atomic,
            OuchClientMessages.ReplaceOrder: self.replace_order_atomic,
            OuchClientMessages.CancelOrder: self.cancel_order_atomic,
            OuchClientMessages.SystemStart: self.system_start_atomic,
            OuchClientMessages.ModifyOrder: None}

    def system_start_atomic(self, system_event_message, timestamp):  
        log.debug('received reset signal at %s.' % timestamp)
        self.order_store.clear_order_store()
        self.order_book.reset_book()
        m = OuchServerMessages.SystemEvent(event_code=b'S', timestamp=timestamp)
        m.meta = system_event_message.meta
        self.outgoing_messages.append(m)

    def accepted_from_enter(self, enter_order_message, timestamp, order_reference_number, order_state=b'L', bbo_weight_indicator=b' '):
        m = OuchServerMessages.Accepted(
            timestamp=timestamp,
            order_reference_number=order_reference_number, 
            order_state=order_state,
            bbo_weight_indicator=bbo_weight_indicator,
            order_token=enter_order_message['order_token'],
            buy_sell_indicator=enter_order_message['buy_sell_indicator'],
            shares=enter_order_message['shares'],
            stock=enter_order_message['stock'],
            price=enter_order_message['price'],
            time_in_force=enter_order_message['time_in_force'],
            firm=enter_order_message['firm'],
            display=enter_order_message['display'],
            capacity=enter_order_message['capacity'],
            intermarket_sweep_eligibility=enter_order_message['intermarket_sweep_eligibility'],
            minimum_quantity=enter_order_message['minimum_quantity'],
            cross_type=enter_order_message['cross_type'])
        m.meta = enter_order_message.meta
        return m

    def cancel_order_from_enter_order(self, enter_order_message, reason = b'U'):
        m = OuchClientMessages.CancelOrder(
            order_token = enter_order_message['order_token'],
            shares = 0
            )
        m.meta = enter_order_message.meta
        return m

    def cancel_order_from_replace_order(self, replace_order_message, reason = b'U'):
        m = OuchClientMessages.CancelOrder(
            order_token = replace_order_message['replacement_order_token'],
            shares = 0
            )
        m.meta = replace_order_message.meta
        return m

    def order_cancelled_from_cancel(self, cancel_order_message, timestamp, amount_canceled, reason=b'U'):
        m = OuchServerMessages.Canceled(timestamp = timestamp,
                            order_token = cancel_order_message['order_token'],
                            decrement_shares = amount_canceled,
                            reason = reason)
        m.meta = cancel_order_message.meta
        return m
    
    def best_quote_update(self, order_message, new_bbo, timestamp):
        m = OuchServerMessages.BestBidAndOffer(timestamp=timestamp, stock=b'AMAZGOOG',
            best_bid=new_bbo.best_bid, volume_at_best_bid=new_bbo.volume_at_best_bid,
            best_ask=new_bbo.best_ask, volume_at_best_ask=new_bbo.volume_at_best_ask 
        )
        m.meta = order_message.meta
        return m

    def process_cross(self, id, fulfilling_order_id, price, volume, timestamp, liquidity_flag = b'?'):
        log.debug('Orders (%s, %s) crossed at price %s, volume %s', id, fulfilling_order_id, price, volume)
        order_message = self.order_store.orders[id].first_message
        fulfilling_order_message = self.order_store.orders[fulfilling_order_id].first_message
        log.debug('%s,%s',order_message,fulfilling_order_message)
        match_number = self.next_match_number
        self.next_match_number += 1
        r1 = OuchServerMessages.Executed(
                timestamp = timestamp,
                order_token = id,
                executed_shares = volume,
                execution_price = price,
                liquidity_flag = liquidity_flag,
                match_number = match_number
                )
        r1.meta = order_message.meta
        self.order_store.add_to_order(r1['order_token'], r1)
        r2 = OuchServerMessages.Executed(
                timestamp = timestamp,
                order_token = fulfilling_order_id,
                executed_shares = volume,
                execution_price = price,
                liquidity_flag = liquidity_flag,
                match_number = match_number
                )
        r2.meta = fulfilling_order_message.meta
        self.order_store.add_to_order(r2['order_token'], r2)
        return [r1, r2]

    def enter_order_atomic(self, enter_order_message, timestamp, executed_quantity = 0):
        order_stored = self.order_store.store_order( 
            id = enter_order_message['order_token'], 
            message = enter_order_message, 
            executed_quantity = executed_quantity)
        if not order_stored:
            log.debug('Order already stored with id %s, order ignored', enter_order_message['order_token'])
            return []
        else:
            time_in_force = enter_order_message['time_in_force']
            enter_into_book = True if time_in_force > 0 else False    
            if time_in_force > 0 and time_in_force < 99998:     #schedule a cancellation at some point in the future
                cancel_order_message = self.cancel_order_from_enter_order( enter_order_message )
                self.loop.call_later(time_in_force, partial(self.cancel_order_atomic, cancel_order_message, timestamp))
            
            enter_order_func = self.order_book.enter_buy if enter_order_message['buy_sell_indicator'] == b'B' else self.order_book.enter_sell
            (crossed_orders, entered_order, new_bbo) = enter_order_func(
                    enter_order_message['order_token'],
                    enter_order_message['price'],
                    enter_order_message['shares'],
                    enter_into_book)
            log.debug("Resulting book: %s", self.order_book)
            m=self.accepted_from_enter(enter_order_message, 
                order_reference_number=next(self.order_ref_numbers),
                timestamp=timestamp)
            self.order_store.add_to_order(m['order_token'], m)
            self.outgoing_messages.append(m)
            cross_messages = [m for ((id, fulfilling_order_id), price, volume) in crossed_orders 
                                for m in self.process_cross(id, fulfilling_order_id, price, volume, timestamp=timestamp)]
            self.outgoing_messages.extend(cross_messages)
            if new_bbo:
                bbo_message = self.best_quote_update(enter_order_message, new_bbo, timestamp)
                self.outgoing_broadcast_messages.append(bbo_message)

    def cancel_order_atomic(self, cancel_order_message, timestamp, reason=b'U'):
        if cancel_order_message['order_token'] not in self.order_store.orders:
            log.debug('No such order to cancel, ignored')
        else:
            store_entry = self.order_store.orders[cancel_order_message['order_token']]
            cancelled_orders, new_bbo = self.order_book.cancel_order(
                id = cancel_order_message['order_token'],
                price = store_entry.first_message['price'],
                volume = cancel_order_message['shares'],
                buy_sell_indicator = store_entry.original_enter_message['buy_sell_indicator'])
            cancel_messages = [  self.order_cancelled_from_cancel(cancel_order_message, timestamp, amount_canceled, reason)
                        for (id, amount_canceled) in cancelled_orders ]

            self.outgoing_messages.extend(cancel_messages) 
            if new_bbo:
                bbo_message = self.best_quote_update(cancel_order_message, new_bbo, timestamp)
                self.outgoing_broadcast_messages.append(bbo_message)

      # """
        # NASDAQ may respond to the Replace Order Message in several ways:
        #     1) If the order for the existing Order Token is no longer live or if the replacement Order
        #         Token was already used, the replacement will be silently ignored.
        #     2) If the order for the existing Order Token is live but the details of the replace are
        #         invalid (e.g.: new Shares >= 1,000,000), a Canceled Order Message will take the
        #         existing order out of the book. The replacement Order Token will not be consumed,
        #         and may be reused in this case.
        #     3) If the order for the existing Order Token is live but the existing order cannot be
        #         canceled (e.g.: the existing Order is a cross order in the late period), there will be a
        #         Reject Message. This reject message denotes that no change has occurred to the
        #         existing order; the existing order remains fully intact with its original instructions.
        #         The Reject Message consumes the replacement Order Token, so the replacement
        #         Order Token may not be reused.
        #     4) If the order for the existing Order Token is live and can be replaced, you will receive
        #         either a Replaced Message or an Atomically Replaced and Canceled Message.
        # """
    def replace_order_atomic(self, replace_order_message, timestamp):
        if replace_order_message['existing_order_token'] not in self.order_store.orders:
            log.debug('Existing token %s unknown, siliently ignoring', replace_order_message['existing_order_token'])
            return []
        elif replace_order_message['replacement_order_token'] in self.order_store.orders:
            log.debug('Replacement token %s unknown, siliently ignoring', replace_order_message['existing_order_token'])
            return []
        else:
            store_entry = self.order_store.orders[replace_order_message['existing_order_token']]
            log.debug('store_entry: %s', store_entry)
            cancelled_orders, new_bbo_post_cancel = self.order_book.cancel_order(
                id = replace_order_message['existing_order_token'],
                price = store_entry.first_message['price'],
                volume = 0,
                buy_sell_indicator = store_entry.original_enter_message['buy_sell_indicator'])  # Fully cancel
            
            if len(cancelled_orders)==0:
                log.debug('No orders cancelled, siliently ignoring')
                return []
            else:
                (id_cancelled, amount_cancelled) = cancelled_orders[0]
                original_enter_message = store_entry.original_enter_message
                first_message = store_entry.first_message
                shares_diff = replace_order_message['shares'] - first_message['shares'] 
                liable_shares = max(0, amount_cancelled + shares_diff )
                if liable_shares == 0:
                    log.debug('No remaining liable shares on the book to replace')
                    #send cancel
                else:
                    self.order_store.store_order(
                            id = replace_order_message['replacement_order_token'], 
                            message = replace_order_message,
                            original_enter_message = original_enter_message)
                    time_in_force = replace_order_message['time_in_force']
                    enter_into_book = True if time_in_force > 0 else False    
                    if time_in_force > 0 and time_in_force < 99998:     #schedule a cancellation at some point in the future
                        cancel_order_message = cancel_order_from_replace_order( replace_order_message )
                        self.loop.call_later(time_in_force, partial(self.cancel_order_atomic, cancel_order_message, timestamp))
                    
                    enter_order_func = self.order_book.enter_buy if original_enter_message['buy_sell_indicator'] == b'B' else self.order_book.enter_sell
                    crossed_orders, entered_order, new_bbo_post_enter = enter_order_func(
                            replace_order_message['replacement_order_token'],
                            replace_order_message['price'],
                            liable_shares,
                            enter_into_book)
                    log.debug("Resulting book: %s", self.order_book)

                    r = OuchServerMessages.Replaced(
                            timestamp=timestamp,
                            replacement_order_token = replace_order_message['replacement_order_token'],
                            buy_sell_indicator=original_enter_message['buy_sell_indicator'],
                            shares=liable_shares,
                            stock=original_enter_message['stock'],
                            price=replace_order_message['price'],
                            time_in_force=replace_order_message['time_in_force'],
                            firm=original_enter_message['firm'],
                            display=replace_order_message['display'],
                            order_reference_number=next(self.order_ref_numbers), 
                            capacity=b'*',
                            intermarket_sweep_eligibility = replace_order_message['intermarket_sweep_eligibility'],
                            minimum_quantity = replace_order_message['minimum_quantity'],
                            cross_type=b'*',
                            order_state=b'L' if entered_order is not None else b'D',
                            previous_order_token=replace_order_message['existing_order_token'],
                            bbo_weight_indicator=b'*'
                            )
                    r.meta = replace_order_message.meta
                    self.outgoing_messages.append(r)
                    self.order_store.add_to_order(r['replacement_order_token'], r)        
                    cross_messages = [m for ((id, fulfilling_order_id), price, volume) in crossed_orders 
                                        for m in self.process_cross(id, 
                                                    fulfilling_order_id, 
                                                    price, 
                                                    volume, 
                                                    timestamp=timestamp)]
                    self.outgoing_messages.extend(cross_messages)

                    bbo_message = None
                    if new_bbo_post_enter:
                        bbo_message = self.best_quote_update(replace_order_message, 
                            new_bbo_post_enter, timestamp)
                    elif new_bbo_post_cancel:
                        bbo_message = self.best_quote_update(replace_order_message, 
                            new_bbo_post_cancel, timestamp)
                    if bbo_message:
                        self.outgoing_broadcast_messages.append(bbo_message)

    async def send_outgoing_broadcast_messages(self):
        while len(self.outgoing_broadcast_messages)>0:
            m = self.outgoing_broadcast_messages.popleft()
            log.debug('Sending message %s', m)
            await self.message_broadcast(m)
            log.debug('Sent message %s', m)    

    async def send_outgoing_messages(self):
        while len(self.outgoing_messages)>0:
            m = self.outgoing_messages.popleft()
            log.debug('Sending message %s', m)
            await self.order_reply(m)
            log.debug('Sent message %s', m)

    async def process_message(self, message):
        log.debug('Processing message %s', message)
        if message.message_type in self.handlers:
            timestamp = nanoseconds_since_midnight()
            self.handlers[message.message_type](message, timestamp)
            await self.send_outgoing_messages()
            await self.send_outgoing_broadcast_messages()
            if self.order_book_logger is not None:
                self.order_book_logger.log_book_order(self.order_book, message, timestamp - self.start_time, self.order_store)
        else:
            log.error("Unknown message type %s", message.message_type)
            return False

    async def modify_order(self, modify_order_message):
        raise NotImplementedError()

