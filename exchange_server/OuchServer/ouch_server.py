"""
Simple Ouch Server to do request echoing
"""

import sys
import asyncio
import asyncio.streams
import configargparse
import logging as log
import itertools
from collections import namedtuple
from functools import partial
import datetime
import pytz

from .ouch_messages import OuchClientMessages, OuchServerMessages

DEFAULT_TIMEZONE = pytz.timezone('US/Pacific')

p = configargparse.ArgParser()
p.add('--port', default=12345)
p.add('--host', default='127.0.0.1', help="Address to bind to / listen on")
options, args = p.parse_known_args()



class ProtocolMessageServer(object): 
    """
    
    """
    ClientInfo = namedtuple('ClientInfo', ['task', 'reader', 'writer'])
    
    def __init__(self, ProtocolMessageTypes):
        self._ProtocolMessageCls = ProtocolMessageTypes.get_message_class()
        self._ProtocolMessageTypes = ProtocolMessageTypes
        self._tokens = itertools.count(0,2)  # evens
        self.server = None # encapsulates the server sockets
        self.clients = {}  # token -> ClientInfo
        self.listeners = {}  # token -> callback    
    @property
    def ProtocolMessageCls(self):
        return self._ProtocolMessageCls
    @property
    def ProtocolMessageTypes(self):
        return self._ProtocolMessageTypes
        
    def _accept_client(self, client_reader, client_writer):
        """
        This method accepts a new client connection and creates a Task
        to handle this client.  self.clients is updated to keep track
        of the new client.
        """
        
        # start a new Task to handle this specific client connection
        client_token = next(self._tokens)
        task = asyncio.Task(self._handle_client_requests(client_token, client_reader))
        
        log.info('client task %s created: %s', str(client_token), task)
        self.clients[client_token] = self.ClientInfo(task, client_reader, client_writer)

        def client_done(task):
            log.info('client task %s done: %s', str(client_token), task)
            del self.clients[client_token]

        task.add_done_callback(client_done)
    
    async def _handle_client_requests(self, client_token, client_reader):
        """
        This method actually does the work to handle the requests for
        a specific client.  The protocol is line oriented, so there is
        a main loop that reads a line with a request and then sends
        out one or more lines back to the client with the result.
        """
        header_size = self._ProtocolMessageCls.get_header_class().size
        while True:
            try:
                header_bytes = (await client_reader.readexactly(header_size))
            except asyncio.IncompleteReadError:
                log.info('no more messages; connection terminated')
                break
            message_type = (self._ProtocolMessageTypes
                            .lookup_by_header_bytes(header_bytes))
            payload_size = message_type.payload_size
            try:
                payload_bytes = (await client_reader.readexactly(payload_size))
            except asyncio.IncompleteReadError as err:
                log.error('Connection terminated mid-packet!')
                break

            client_msg = message_type.from_bytes(payload_bytes, header=False)
            client_msg.meta = client_token
            await self.broadcast_to_listeners(client_msg)
            
    async def send_server_response(self, server_msg):
        client_token = server_msg.meta
        client_writer = self.clients[client_token].writer
        client_writer.write(bytes(server_msg))
        await client_writer.drain()

    async def broadcast_server_message(self, server_msg):
        for client in self.clients.values():
            client.writer.write(bytes(server_msg))
        for client in self.clients.values():
            await client.writer.drain()
    
    def register_listener(self, callback):
        listener_token = next(self._tokens)
        self.listeners[listener_token] = callback
        log.info('added listener %s', str(listener_token))
        return listener_token
    
    def deregister_listener(self, listener_token):
        del self.listeners[listener_token]
        log.info('removed listener %s', str(listener_token))
    
    async def broadcast_to_listeners(self, client_msg):
        for callback in self.listeners.values():
            await callback(client_msg)
        
    def start(self, loop):
        """
        Starts the server, listening on the specified port.
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
        Stops the server, i.e. closes the listening socket(s).
        This method runs the loop until the server sockets are closed.
        """
        if self.server is not None:
            self.server.close()
            loop.run_until_complete(self.server.wait_closed())
            self.server = None

def nanoseconds_since_midnight(tz=DEFAULT_TIMEZONE):
    now = datetime.datetime.now(tz=tz)
    timestamp = 0  # since midnight
    timestamp += now.hour
    timestamp *= 60  # hours -> minutes
    timestamp += now.minute
    timestamp *= 60  # minutes -> seconds
    timestamp += now.second
    timestamp *= 10**6  # seconds -> microsecnds
    timestamp += now.microsecond
    timestamp *= 10**3  # microseconds -> nanoseconds
    return timestamp

order_ref_numbers = itertools.count(1, 2)  # odds
async def message_acker(callback, message):
    if message.message_type is not OuchClientMessages.EnterOrder:
        log.info('unhandled message type %s', message.message_type.name)
        return
    fields = dict(message.iteritems())
    fields['bbo_weight_indicator'] = b' '
    fields['order_reference_number'] = next(order_ref_numbers)
    fields['timestamp'] = nanoseconds_since_midnight()
    fields['order_state'] = b'L'
    
    response = OuchServerMessages.Accepted(**fields)
    response.meta = message.meta
    await callback(response)

def main():
    log.basicConfig(level=log.DEBUG)

    log.debug(options)

    loop = asyncio.get_event_loop()

    # creates a server and starts listening to TCP connections
    server = ProtocolMessageServer(OuchClientMessages)
    server.register_listener(partial(message_acker, server.send_server_response))
    server.start(loop)
    try:
        loop.run_forever()
    finally:
        loop.close()

if __name__ == '__main__':
    main()
