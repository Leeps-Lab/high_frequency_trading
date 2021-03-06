from .outbound_message_primitives import MessageFactory, InternalEventMessage


class MarketReadyToStartMessage(InternalEventMessage):

    required_fields = ('market_id', 'subsession_id')


class MarketReadyToEndMessage(InternalEventMessage):

    required_fields = ('market_id', 'subsession_id')


class MarketStartMessage(InternalEventMessage):

    required_fields = ('market_id', 'subsession_id', 'session_duration')


class MarketEndMessage(InternalEventMessage):

    required_fields = ('market_id', 'subsession_id')


class ReferencePriceChangeMessage(InternalEventMessage):

    required_fields = ('reference_price', 'market_id', 'subsession_id')


class SignedVolumeChangeMessage(InternalEventMessage):

    required_fields = (
        'signed_volume', 'market_id', 'subsession_id')


class BBOChangeMessage(InternalEventMessage):

    required_fields = (
        'best_bid', 'best_offer', 'volume_at_best_bid', 'volume_at_best_offer',
        'next_offer', 'next_bid', 'market_id', 'subsession_id')

class PostBatchMessage(InternalEventMessage):

    required_fields = (
        'best_bid', 'best_offer', 'volume_at_best_bid', 'volume_at_best_offer',
        'next_offer', 'next_bid', 'market_id', 'subsession_id')

class ExternalFeedChangeMessage(InternalEventMessage):

    required_fields = (
        'market_id', 'subsession_id', 'e_best_bid', 'e_best_offer', 
        'e_signed_volume')

class ELOInternalEventMessageFactory(MessageFactory):

    message_types = {
        'market_ready_to_start': MarketReadyToStartMessage,
        'market_ready_to_end': MarketReadyToEndMessage,
        'reference_price_change': ReferencePriceChangeMessage,
        'signed_volume_change': SignedVolumeChangeMessage,
        'external_feed_change': ExternalFeedChangeMessage,
        'bbo_change': BBOChangeMessage,
        'post_batch': PostBatchMessage,
        'market_start': MarketStartMessage,
        'market_end': MarketEndMessage
    }