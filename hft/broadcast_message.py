from .outbound_message_primitives import (BroadcastWSMessage, MessageFactory)


class BBOBroadcastMessage(BroadcastWSMessage):

    required_fields = (
        'market_id', 'best_bid', 'best_offer', 'volume_at_best_bid', 
        'volume_at_best_offer')
    required_field_types = (int, int, int, int, int)


class OrderConfirmedBroadcastMessage(BroadcastWSMessage):

    required_fields = (
        'market_id', 'player_id', 'order_token', 'price', 'buy_sell_indicator',
        'time_in_force')
    required_field_types = (int, int, str, int, str, int)


class OrderReplacedBroadcastMessage(BroadcastWSMessage):

    required_fields = (
        'market_id', 'player_id', 'price', 'order_token', 'old_token', 
        'old_price', 'buy_sell_indicator')
    required_field_types = (int, int, int, str, str, int, str)


class OrderCanceledBroadcastMessage(BroadcastWSMessage):

    required_fields = (
        'market_id', 'player_id', 'order_token',  'price', 'buy_sell_indicator')
    required_field_types = (int, int, str, int, str)


class OrderExecutedBroadcastMessage(BroadcastWSMessage):

    required_fields = (
        'market_id', 'player_id', 'order_token',  'price', 'buy_sell_indicator',
        'inventory', 'execution_price')
    required_field_types = (int, int, str, int, str, int, int)


class SystemEventBroadcastMessage(BroadcastWSMessage):
    required_fields = ('market_id', 'code')
    required_field_types = (int, str)    


class RoleConfirmedBroadcastMessage(BroadcastWSMessage):
    required_fields = ('market_id', 'player_id', 'role_name')
    required_field_types = (int, int, str)  


class SignedVolumeBroadcastMessage(BroadcastWSMessage):
    required_fields = ('market_id', 'signed_volume')
    required_field_types = (int, float) 


class ExternalFeedBroadcastMessage(BroadcastWSMessage):
    required_fields = ('market_id', 'e_best_bid', 'e_best_offer', 'e_signed_volume')
    required_field_types = (int, int, int, float) 


class ReferencePriceBroadcastMessage(BroadcastWSMessage):
    required_fields = ('market_id', 'reference_price')
    required_field_types = (int, int) 


class SpeedConfirmBroadcastMessage(BroadcastWSMessage):
    required_fields = ('market_id', 'player_id', 'value')
    required_field_types = (int, int, bool)  

class SliderConfirmBroadcastMessage(BroadcastWSMessage):
    required_fields = ('market_id', 'player_id', 'a_x', 'a_y', 'a_z')
    required_field_types = (int, int, float, float, float)  

class PostBatchBroadcastMessage(BroadcastWSMessage):
    required_fields = (
        'market_id', 'best_bid', 'best_offer', 'volume_at_best_bid', 
        'volume_at_best_offer')
    required_field_types = (int,)


class ELOBroadcastMessageFactory(MessageFactory):

    message_types = {
        'bbo': BBOBroadcastMessage,
        'confirmed': OrderConfirmedBroadcastMessage,
        'replaced': OrderReplacedBroadcastMessage,
        'canceled': OrderCanceledBroadcastMessage,
        'executed': OrderExecutedBroadcastMessage,
        'system_event': SystemEventBroadcastMessage,
        'role_confirm': RoleConfirmedBroadcastMessage,
        'signed_volume': SignedVolumeBroadcastMessage,
        'external_feed': ExternalFeedBroadcastMessage,
        'reference_price': ReferencePriceBroadcastMessage,
        'speed_confirm': SpeedConfirmBroadcastMessage,
        'slider_confirm': SliderConfirmBroadcastMessage,
        'post_batch': PostBatchBroadcastMessage,
    }
