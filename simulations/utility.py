from hft.incoming_message import IncomingWSMessage
from hft.market_components import hft_facts
from random import randint, choice
import time

def generate_random_test_orders(num_orders, session_duration):
    return iter(
            {'arrival_time': randint(1, 60),
            'price': randint(100, 110),
            'buy_sell_indicator': choice(['B', 'S']),
            'time_in_force': choice([10, 15, 20])
            } for o in range(50))


class MockMarket:

    def __init__(self):
        self.time_origin = time.time()
        self.bbo = hft_facts.BestBidOffer()
        self.signed_volume = hft_facts.SignedVolume(k_signed_volume=0.01)
        self.history = []

    def reset(self):
        self.__init__()
    
    def handle_event(self, event):
        timestamp = round((time.time() - self.time_origin), 3)
        if event.event_type == 'E':
            kwargs = event.to_kwargs()
            # as bbo is an input to signed volume updates
            kwargs.update(self.bbo.to_kwargs())
            self.signed_volume.update(**kwargs)
        elif event.event_type == 'Q':
            self.bbo.update(**event.to_kwargs())
            if self.bbo.has_changed:
                self.record_history(timestamp)
    
    def record_history(self, timestamp):
        market_state = {'timestamp': timestamp}
        market_state.update(self.signed_volume.to_kwargs())
        market_state.update(self.bbo.to_kwargs())
        self.history.append(market_state)
        print(self.history[-1])

 
class MockWSMessage(IncomingWSMessage):

    sanitizer_cls = None

    def translate(self, message):
        return message

