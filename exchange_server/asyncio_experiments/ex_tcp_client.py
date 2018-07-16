import sys
import asyncio
import asyncio.streams



def main():
    async def client():
        reader, writer = await asyncio.streams.open_connection(
            '127.0.0.1', 12345, loop=loop)

        def send(msg):
            print("> " + msg)
            writer.write((msg + '\n').encode("utf-8"))

        async def recv():
            msgback = (await reader.readline()).decode("utf-8").rstrip()
            print("< " + msgback)
            return msgback

        # send a line
        send("add 1 2")
        msg = await recv()

        await asyncio.sleep(2.0)
        send("repeat 5 hello")
        msg = await recv()
        assert msg == 'begin'
        while True:
            await asyncio.sleep(2.0)
            msg = await recv()
            if msg == 'end':
                break

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