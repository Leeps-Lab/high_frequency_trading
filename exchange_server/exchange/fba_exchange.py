import logging as log
import asyncio
from exchange.exchange import Exchange
from OuchServer.ouch_server import nanoseconds_since_midnight
from OuchServer.ouch_messages import OuchServerMessages

class FBAExchange(Exchange):
    def __init__(self, interval, *args, **kwargs):
        self.interval = interval
        super().__init__(*args, **kwargs)

    def start(self):
        asyncio.ensure_future(self.run_batch_repeating())

    def run_batch_atomic(self):
        timestamp = nanoseconds_since_midnight()
        crossed_orders = self.order_book.batch_process()
        cross_messages = [m for ((id, fulfilling_order_id), price, volume) 
                                            in crossed_orders 
                            for m in self.process_cross(
                                id, fulfilling_order_id, 
                                price, volume, 
                                timestamp=timestamp)]
        self.outgoing_messages.extend(cross_messages)

    async def run_batch_repeating(self):
        while True:
            log.debug('Starting batch at %s', self.loop.time())
            timestamp = nanoseconds_since_midnight()
            await self.message_broadcast(
                OuchServerMessages.SystemEvent(
                    event_code=b'B',
                    timestamp=timestamp))
            self.run_batch_atomic()
            await self.message_broadcast(
                OuchServerMessages.SystemEvent(
                    event_code=b'P',
                    timestamp=nanoseconds_since_midnight()))
            await self.send_outgoing_messages()
            self.order_book_logger.log_book(self.order_book, timestamp, self.order_store)
            log.debug('Ended batch at %s', self.loop.time())
            await asyncio.sleep(self.interval - (self.loop.time() % self.interval))