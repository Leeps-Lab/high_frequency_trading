from . import utility
from .exchange import send_exchange
from .translator import LeepsOuchTranslator
from . import client_messages

def process_response(message_queue):
    def exchange(message):
        exchange_message_type = message['type']     
        order_data = utility.pretranslate_hacks(exchange_message_type, message['order_info'])
        host, port, delay = message['host'], message['port'], message['delay']
        bytes_message = LeepsOuchTranslator.encode(exchange_message_type, **order_data)
        send_exchange(host, port, bytes_message, delay)
    def broadcast(message):
        message_type, channels_group_id = message['type'], message['group_id']
        broadcast_data = message['message']
        client_messages.broadcast(message_type, channels_group_id, **broadcast_data)
    while message_queue:
        message = message_queue.popleft()
        message_type, message_payload = message['message_type'], message['payload']
        handler = locals()[message_type]
        print('\nOUTGOING:%s\n' % message)
        handler(message_payload)
