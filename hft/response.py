from . import utility
from .exchange import send_exchange
from .translator import LeepsOuchTranslator
from . import outbound_subject_messages 

def process_response(message):
    def exchange(message):
        exchange_message_type = message['type']     
        order_data = utility.pretranslate_hacks(exchange_message_type, message['order_info'])
        host, port, delay = message['host'], message['port'], message['delay']
        bytes_message = LeepsOuchTranslator.encode(exchange_message_type, **order_data)
        send_exchange(host, port, bytes_message, delay)
    def broadcast(message):
        message_type = message['type']
        outbound_subject_messages.broadcast(message_type, **message)
    message_type, message_payload = message['message_type'], message['payload']
    handler = locals()[message_type]
    handler(message_payload)
