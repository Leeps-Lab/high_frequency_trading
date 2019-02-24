from .outbound_message_primitives import (OutboundExchangeMessage, BroadcastWSMessage,
    BroadcastMessageFactory)

class BBOBroadcastMessage(BroadcastWSMessage):

    required_fields = ('market_id', 'best_bid', 'best_offer', 'volume_at_best_bid', 
        'volume_at_best_offer')
    required_field_types = (int, int, int, int, int)

class OrderConfirmedBroadcastMessage(BroadcastWSMessage):

    required_fields = ('market_id', 'player_id', 'order_token', 'price', 'buy_sell_indicator')
    required_field_types = (int, int, str, int, str)

class OrderReplacedBroadcastMessage(BroadcastWSMessage):

    required_fields = ('market_id', 'player_id', 'price', 'order_token', 'old_token', 'old_price',
        'buy_sell_indicator')
    required_field_types = (int, int, int, str, str, int, str)

class OrderCanceledBroadcastMessage(BroadcastWSMessage):

    required_fields = ('market_id', 'player_id', 'order_token',  'price', 'buy_sell_indicator')
    required_field_types = (int, int, str, int, str)

class OrderExecutedBroadcastMessage(BroadcastWSMessage):

    required_fields = ('market_id', 'player_id', 'order_token',  'price', 'buy_sell_indicator',
        'inventory', 'cash')
    required_field_types = (int, int, str, int, str, int, int)

class SystemEventBroadcastMessage(BroadcastWSMessage):
    required_fields = ('market_id', 'code')
    required_field_types = (int, str)    

class RoleConfirmedBroadcastMessage(BroadcastWSMessage):
    required_fields = ('player_id', 'role_name')
    required_field_types = (int, str)  

class OrderImbalanceBroadcastMessage(BroadcastWSMessage):
    required_fields = ('market_id', 'value')
    required_field_types = (int, float) 

class ELOTakerQuoteBroadcastMessage(BroadcastWSMessage):
    required_fields = ('market_id', 'bid', 'offer')
    required_field_types = (int, int, int)

class ReferencePriceBroadcastMessage(BroadcastWSMessage):
    required_fields = ('market_id', 'price')
    required_field_types = (int, int)  

class ELOBroadcastMessageFactory(BroadcastMessageFactory):

    message_types = {
        'bbo': BBOBroadcastMessage,
        'confirmed': OrderConfirmedBroadcastMessage,
        'replaced': OrderReplacedBroadcastMessage,
        'canceled': OrderCanceledBroadcastMessage,
        'executed': OrderExecutedBroadcastMessage,
        'system_event': SystemEventBroadcastMessage,
        'role_confirm': RoleConfirmedBroadcastMessage,
        'order_imbalance': OrderImbalanceBroadcastMessage,
        'reference_price': ReferencePriceBroadcastMessage,
        'elo_quote_cue': ELOTakerQuoteBroadcastMessage
    }