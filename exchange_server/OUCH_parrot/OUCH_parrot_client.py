"""
Simple TCP client that sends random OUCH messages to the parrot server.
"""

import sys
import asyncio
import asyncio.streams
import configargparse
import logging as log
import binascii
from simple_OUCH import *
import random

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

        def send(ouch_message):
            message = binascii.b2a_hex(ouch_message.encode()).decode('ascii')
            
            log.debug("Sending hex encoded OUCH message: %s", message)

            writer.write("{}\n".format(message).encode("ascii"))

        async def recv():
            msgback = (await reader.readline()).decode("ascii").rstrip()
            print("< " + msgback)
            return msgback

        # send a line
        while True:
            m = EnterOrderOUCHMessage(
                order_token = b'00000000000000', 
                buy_sell_indicator=b'B', 
                shares=random.randrange(5,15), 
                stock=b'ABC', 
                price=random.randrange(21, 59))
            log.info("Sending OUCH message: %s", m)

            send(m)

            await writer.drain()

            raw_response = await recv()
            response = parse_OUCH(binascii.a2b_hex(raw_response))
            log.info("Received response OUCH: %s", response)    
            if response == 'end':
                break

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