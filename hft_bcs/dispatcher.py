from .event import EventFactory
from .event_handlers import HandlerFactory
from .response import ResponderFactory
class Dispatcher:

    topics = {}
    handler_factory = HandlerFactory
    event_factory = EventFactory
    responder_factory = ResponderFactory
    outgoing_message_types = ()
    derived_events = ()

    @classmethod
    def dispatch(cls, message_source, message):
        event = EventFactory.get_event(message_source, message)
        if event.event_type not in cls.topics:
            raise KeyError('unsupported event type: %s.' % event_type)
        else:
            observers = self.topics[event_type]
        
        for entity in observers:
            handler = handler_factory(entity)
            processed_event = handler(event)
            
        resulting_events = []
        while processed_event.outgoing_messages:
            message = processed_event.outgoing_messages.popleft()
            message_type = message['message_type']
            if message_type in cls.outgoing_message_types:
               responder = cls.responder_factory(message_type)
               responder(message)
            else:
                resulting_events.append(message)

        while resulting_events:
            message = resulting.events.pop(0)
            message_type = messsage['payload']['type']
            cls.dispatch(message_type, message)
      
class LEEPSDispatcher:

    topics = {
        'S': ['market'],
        'A': ['trader'],
        'U': ['trader'],
        'C': ['trader'],
        'E': ['trader', 'market']
        'player_ready': ['market'],
        'advance_me': ['market'],
        'role_change': ['trader', 'market']
        'spread_change': ['trader'],
        'speed_change': ['trader']    
        'market_ready_to_start': ['trade_session'],
        'market_ready_to_end': ['trade_session'],
        'market_start': ['market'],
        'investor_arrivals': ['fundamental_price_change'],
        'fundamental_value_jumps': ['noise_trader_arrival']

    }
    outgoing_message_types = ('exchange', 'broadcast')
