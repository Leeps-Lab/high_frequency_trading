"""
Client for simple Ouch Server
"""

import sys
import asyncio
import asyncio.streams
import configargparse
import logging as log
# import binascii
from random import randrange
import itertools

from OuchServer.ouch_messages import OuchClientMessages, OuchServerMessages

p = configargparse.ArgParser()
p.add('--port', default=12345)
p.add('--host', default='127.0.0.1', help="Address of server")
options, args = p.parse_known_args()

def main():
    log.basicConfig(level=log.DEBUG)
    log.debug(options)

    async def client():
        reader, writer = await asyncio.streams.open_connection(
            options.host, 
            options.port, 
            loop=loop)

        async def send(request):
            writer.write(bytes(request))
            await writer.drain()

        async def recv():
            try:
                header = (await reader.readexactly(1))
            except asyncio.IncompleteReadError:
                log.error('connection terminated without response')
                return None
            log.debug('Received Ouch header as binary: %r', header)
            log.debug('bytes: %r', list(header))
            message_type = OuchServerMessages.lookup_by_header_bytes(header)
            try:
                payload = (await reader.readexactly(message_type.payload_size))
            except asyncio.IncompleteReadError as err:
                log.error('Connection terminated mid-packet!')
                return None
            log.debug('Received Ouch payload as binary: %r', payload)
            log.debug('bytes: %r', list(payload))

            response_msg = message_type.from_bytes(payload, header=False)
            return response_msg

        # send a line
        while True:
            message_type = OuchClientMessages.EnterOrder
            
            for index in itertools.count():
                request = message_type(
                    order_token='{:014d}'.format(index).encode('ascii'),
                    buy_sell_indicator=b'B',
                    shares=randrange(1,10**6-1),
                    stock=b'AMAZGOOG',
                    price=randrange(1,10**9-100),
                    time_in_force=randrange(0,99999),
                    firm=b'OUCH',
                    display=b'N',
                    capacity=b'O',
                    intermarket_sweep_eligibility=b'N',
                    minimum_quantity=1,
                    cross_type=b'N',
                    customer_type=b' ')
                print('send message: ', request)
                log.info("Sending Ouch message: %s", request)
                await send(request)
                response = await recv()
                print('recv message: ', response)
                log.info("Received response Ouch message: %s", response)    
                await asyncio.sleep(4.0)
            
        writer.close()
        await asyncio.sleep(0.5)


    loop = asyncio.get_event_loop()

    # creates a client and connects to our server
    try:
        loop.run_until_complete(client())
    finally:
        loop.close()

if __name__ == '__main__':
    main()
