from .event import EventFactory
from .event_handlers import HandlerFactory
from .response import process_response
# from otree.timeout.tasks import hft_background_task
from .output import hft_event_checkpoint

class Dispatcher:

    topics = {}
    handler_factory = HandlerFactory
    event_factory = EventFactory
    responder = process_response
    outgoing_message_types = ()

    @classmethod
    def dispatch(cls, message_source, message, **kwargs):
        event = EventFactory.get_event(message_source, message, **kwargs)
        if event.event_type not in cls.topics:
            raise KeyError('unsupported event type: %s.' % event.event_type)
        else:
            observers = cls.topics[event.event_type]
            
        for entity in observers:
            handler = cls.handler_factory.get_handler(entity)
            event = handler(event)
        print(event.event_type) 
        # hft_background_task(hft_event_checkpoint, event)   
        resulting_events = []
        while event.outgoing_messages:
            message = event.outgoing_messages.popleft()
            message_type = message['message_type']
            if message_type in cls.outgoing_message_types:
                cls.responder(message)
            else:
                resulting_events.append(message)

        while resulting_events:
            message = resulting_events.pop(0)
            message_type = message['message_type']
            cls.dispatch(message_type, message)
      
class LEEPSDispatcher(Dispatcher):

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
        'market_start': ['market'],
        'market_end': ['market'],
        'order_by_arrow': ['trader'],
        'investor_arrivals': ['noise_trader_arrival'],
        'fundamental_value_jumps': ['fundamental_price_change'],
        'bbo_change': ['role_based_events'],
        'order_imbalance_change': ['role_based_events'],      
    }
    outgoing_message_types = ('exchange', 'broadcast')
