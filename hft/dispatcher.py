from .incoming_message import IncomingMessageFactory
from .event import EventFactory
from .event_handler import EventHandlerFactory
from .response import process_response, new_broadcast
from otree.timeout.tasks import hft_background_task
import logging

log = logging.getLogger(__name__)


class Dispatcher:

    topics = {}
    handler_factory = EventHandlerFactory
    event_factory = EventFactory
    message_factory = IncomingMessageFactory
    responder = process_response
    market_environment = None
    outgoing_message_types = ()

    @classmethod
    def dispatch(cls, message_source, message, **kwargs):
        incoming_message = cls.message_factory.get_message(
            message_source, message, cls.market_environment, **kwargs)
        event = EventFactory.get_event(message_source, incoming_message, **kwargs)
        if event.event_type not in cls.topics:
            log.warning('unsupported event type: %s.' % event.event_type)
            return
        else:
            observers = cls.topics[event.event_type]

        for topic in observers:
            handler = cls.handler_factory.get_handler(
                event, topic, cls.market_environment)
            event = handler.handle()

        log.debug(
            '{event.reference_no}:{event.event_source}:{event.event_type}:{event.player_id}'.format(
             event=event))
      # log.debug(event)

        while event.outgoing_messages:
            message = event.outgoing_messages.popleft()
            message_type = message['message_type']
            if message_type in cls.outgoing_message_types:
                cls.responder(message)

        while event.broadcast_msgs:
            message = event.broadcast_msgs.pop()
            new_broadcast(message)

        while event.internal_event_msgs:
            message = event.internal_event_msgs.pop()
            cls.dispatch('internal_event', message)


class ELODispatcher(Dispatcher):

    market_environment = 'elo'
    topics = {
        'S': ['market'],
        'A': ['trader'],
        'U': ['trader'],
        'C': ['trader'],
        'E': ['trader', 'market'],
        'Q': ['market'],
        'player_ready': ['market'],
        'advance_me': ['market'],
        'role_change': ['market', 'trader_role_change'],
        'spread_change': ['trader'],
        'speed_change': ['trader'],
        'market_ready_to_start': ['trade_session'],
        'market_ready_to_end': ['trade_session'],
        'market_start': ['market'],
        'market_end': ['market', 'marketwide_events'],
        'order_entered': ['trader'],
        'investor_arrivals': ['trader'],
        'external_feed': ['market'],
        'bbo_change': ['marketwide_events'],
        'signed_volume_change': ['marketwide_events'],
        'reference_price_change': ['marketwide_events'],
        'slider': ['trader']}
    outgoing_message_types = ('exchange', 'broadcast')
