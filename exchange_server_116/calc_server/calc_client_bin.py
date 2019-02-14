"""
Client for simple Calc Server
"""

import sys
import asyncio
import asyncio.streams
import configargparse
import logging as log
# import binascii
import random

import calc_messages


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
            # data = binascii.b2a_hex(calc_messages.pack_calc_message(request))
            data = calc_messages.pack_calc_message(request)
            
            log.debug('Sending Calc message as binary: %r', data)
            log.debug('bytes: %r', list(data))

            writer.write(data)  # + b' \n')
            await writer.drain()

        async def recv():
            data = None
            while not data:
                try:
                    data = (await reader.readexactly(1))
                except asyncio.IncompleteReadError:
                    log.error('connection terminated without response')
                    return None
                if not data.decode().strip():
                    data = None
                    continue
            log.debug('Received Calc header as binary: %r', data)
            log.debug('bytes: %r', list(data))
            header = data  # binascii.a2b_hex(data)
            payload_len = calc_messages.get_calc_message_payload_len(header)
            try:
                data = (await reader.readexactly(payload_len))
            except asyncio.IncompleteReadError as err:
                log.error('Connection terminated mid-packet!')
                return None
            log.debug('Received Calc payload as binary: %r', data)
            log.debug('bytes: %r', list(data))
            payload = data  # binascii.a2b_hex(data)

            response_msg = calc_messages.unpack_calc_message(header, payload)
            return response_msg

        # send a line
        while True:
            message_type = random.choice([b'B', b'T'])
            binary_operator = random.choice([b'+', b'-'])
            trinary_operator = random.choice([b'MED', b'AVG'])

            request = calc_messages.calc_messages[message_type](
                binary_operator=binary_operator,
                trinary_operator=trinary_operator,
                operand_1=random.randrange(2**32),
                operand_2=random.randrange(2**32),
                operand_3=random.randrange(2**32)
            )

            print('send message: ', request)
            log.info("Sending Calc message: %s", request)
            await send(request)
            response = await recv()
            print('recv message: ', response)
            log.info("Received response Calc message: %s", response)    
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
