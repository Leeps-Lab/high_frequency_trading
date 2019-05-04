from . import utility
from .exchange import send_exchange
from .translator import LeepsOuchTranslator 
from channels import Group as CGroup, Channel

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

def new_broadcast(message):
    channel_group = CGroup(str(message.market_id))
    channel_group.send({"text": message.to_json()}) 

def new_exchange(message):
    # exchange_message_type = message.type    
    # order_data = utility.pretranslate_hacks(exchange_message_type, message['order_info'])
    # host, port, delay = message['host'], message['port'], message['delay']
    # bytes_message = LeepsOuchTranslator.encode(exchange_message_type, **order_data)
    send_exchange(
        message.exchange_host, message.exchange, message.translate(), 
        message.delay)