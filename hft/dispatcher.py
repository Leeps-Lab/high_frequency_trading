from .incoming_message import IncomingMessageFactory
from .event import EventFactory
from .event_handler import EventHandlerFactory
from .broadcaster import Broadcaster
from otree.timeout.tasks import hft_background_task
from .exchange import send_exchange
import logging

log = logging.getLogger(__name__)

class DispatcherFactory:

    @staticmethod
    def get_dispatcher(session_format):
        return ELODispatcher

class Dispatcher:

    topics = {}
    handler_factory = EventHandlerFactory
    event_factory = EventFactory
    message_factory = IncomingMessageFactory
    market_environment = None
    outgoing_message_types = ()

    @classmethod
    def dispatch(cls, message_source, message, broadcaster=Broadcaster(), **kwargs):
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
        #log.debug(event)


        while event.exchange_msgs:
            message = event.exchange_msgs.pop()
            send_exchange(
                message.exchange_host, message.exchange_port, message.translate(), 
                message.delay)

        while event.broadcast_msgs:
            message = event.broadcast_msgs.pop()
            broadcaster.broadcast(message, batch=True)

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
        'role_change': ['market', 'trader'],
        'spread_change': ['trader'],
        'speed_change': ['trader'],
        'market_ready_to_start': ['trade_session'],
        'market_ready_to_end': ['trade_session'],
        'market_start': ['market', 'marketwide_events'],
        'market_end': ['market', 'marketwide_events'],
        'order_entered': ['trader'],
        'investor_arrivals': ['trader'],
        'external_feed': ['market'],
        'bbo_change': ['marketwide_events'],
        'signed_volume_change': ['marketwide_events'],
        'reference_price_change': ['marketwide_events'],
        'external_feed_change': ['marketwide_events'],
        'slider': ['trader']}
    outgoing_message_types = ('exchange', 'broadcast')
