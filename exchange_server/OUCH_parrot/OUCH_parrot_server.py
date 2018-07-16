"""
Simple TCP server that accepts OUCH messages, decodes them, and then parrots them back to you.
"""

import sys
import asyncio
import asyncio.streams
import configargparse
import logging as log
import binascii
from simple_OUCH import *


p = configargparse.ArgParser()
p.add('--port', default=12345)
p.add('--host', default='127.0.0.1', help="Address to bind to / listen on")
options, args = p.parse_known_args()

class OUCHParrotServer:
    """
    
    """

    def __init__(self):
        self.server = None # encapsulates the server sockets

        # this keeps track of all the clients that connected to our
        # server.  It can be useful in some cases, for instance to
        # kill client connections or to broadcast some data to all
        # clients...
        self.clients = {} # task -> (reader, writer)

    def _accept_client(self, client_reader, client_writer):
        """
        This method accepts a new client connection and creates a Task
        to handle this client.  self.clients is updated to keep track
        of the new client.
        """

        # start a new Task to handle this specific client connection
        task = asyncio.Task(self._handle_client(client_reader, client_writer))
        self.clients[task] = (client_reader, client_writer)

        def client_done(task):
            print("client task done:", task, file=sys.stderr)
            del self.clients[task]

        task.add_done_callback(client_done)

    
    async def _handle_client(self, client_reader, client_writer):
        """
        This method actually does the work to handle the requests for
        a specific client.  The protocol is line oriented, so there is
        a main loop that reads a line with a request and then sends
        out one or more lines back to the client with the result.
        """
        while True:
            data = (await client_reader.readline()).decode("ascii").rstrip()
            if not data: # an empty string means the client disconnected
                break
            log.debug("Received data: %s", data)    
            
            message = parse_OUCH(binascii.a2b_hex(data))
            
            log.info("Received OUCH message: %s", message)

            message.shares = message.shares*2

            log.info("Replying with OUCH message with twice the shares: %s", message)

            response = binascii.b2a_hex(message.encode()).decode('ascii')
            
            log.debug("Sending hex encoded message: %s", response)

            client_writer.write("{}\n".format(response).encode("ascii"))

            # This enables us to have flow control in our connection.
            await client_writer.drain()

    def start(self, loop):
        """
        Starts the TCP server, so that it listens on port 12345.
        For each client that connects, the accept_client method gets
        called.  This method runs the loop until the server sockets
        are ready to accept connections.
        """
        self.server = loop.run_until_complete(
            asyncio.streams.start_server(self._accept_client,
                                         options.host, 
                                         options.port,
                                         loop=loop))

    def stop(self, loop):
        """
        Stops the TCP server, i.e. closes the listening socket(s).
        This method runs the loop until the server sockets are closed.
        """
        if self.server is not None:
            self.server.close()
            loop.run_until_complete(self.server.wait_closed())
            self.server = None


def main():
    log.basicConfig(level=log.DEBUG)

    log.debug(options)

    loop = asyncio.get_event_loop()

    # creates a server and starts listening to TCP connections
    server = OUCHParrotServer()
    server.start(loop)
    try:
        loop.run_forever()
    finally:
        loop.close()

if __name__ == '__main__':
    main()