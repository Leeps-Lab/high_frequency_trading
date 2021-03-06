from .outbound_message_primitives import OutboundExchangeMessage, MessageFactory


class EnterOrderMessage(OutboundExchangeMessage):
    required_fields = (
        'subsession_id',
        'order_token', 'buy_sell_indicator', 'price', 'time_in_force', 'firm',
        'shares', 'stock', 'exchange_host', 'exchange_port', 'delay', 'midpoint_peg')


class ReplaceOrderMessage(OutboundExchangeMessage):
    required_fields = (
        'subsession_id',
        'existing_order_token', 'replacement_order_token', 'price', 'replace_price',
        'time_in_force', 'exchange_host', 'exchange_port', 'delay', 'shares')


class CancelOrderMessage(OutboundExchangeMessage):
    required_fields = ('subsession_id', 'order_token', 'exchange_host', 
        'exchange_port', 'delay', 'shares')


class ResetMessage(OutboundExchangeMessage):
    required_fields = ('subsession_id', 'event_code', 'timestamp', 'exchange_host', 
        'exchange_port', 'delay')


class ExternalFeedChangeMessage(OutboundExchangeMessage):
    required_fields = (
        'subsession_id', 'e_best_bid', 'e_best_offer', 
        'e_signed_volume', 'exchange_host', 'exchange_port', 'delay')


class OutboundExchangeMessageFactory(MessageFactory):
    message_types = {
        'enter': EnterOrderMessage,
        'replace': ReplaceOrderMessage,
        'cancel': CancelOrderMessage,
        'reset_exchange': ResetMessage,
        'external_feed': ExternalFeedChangeMessage,
    }