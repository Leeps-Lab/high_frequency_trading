from hft.incoming_message import IncomingWSMessage
from hft.market_components import hft_facts
from random import randint, choice
from twisted.internet import reactor
import time

def generate_random_test_orders(num_orders, session_duration):
    return iter(
            {'arrival_time': randint(10, 60) / 10,
            'price': randint(100, 110),
            'buy_sell_indicator': choice(['B', 'S']),
            'time_in_force': choice([10, 15, 20])
            } for o in range(50))


class MockMarket:

    export_file_meta_table = {
        'arrival_time': 'timestamp',
        'e_best_bid': 'best_bid',
        'e_best_offer': 'best_offer',
        'e_signed_volume': 'signed_volume'
    }
    export_file_headers = (
        'arrival_time', 'market_id_in_subsession','e_best_bid', 'e_best_offer', 'e_signed_volume')
    export_file_defaults = {'market_id_in_subsession': 1}

    def __init__(self, session_duration=60, dump_path=None):
        self.time_origin = time.time()
        self.bbo = hft_facts.BestBidOffer()
        self.signed_volume = hft_facts.SignedVolume(k_signed_volume=0.01)
        self.history = []
        self.session_duration = session_duration
        self.dump_path = dump_path
        # works but temporary
        print(self.dump_path)
        reactor.callLater(self.session_duration, self.dump_history)

    def reset(self):
        self.signed_volume.reset_timer()

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
    
    def dump_history(self):
        try:
            import csv
            path = self.dump_path
            if path is not None:
                with open(path, 'w') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=self.export_file_headers)
                    writer.writeheader()
                    for row in self.history:
                        export_row = self.from_history_row_to_export_row(row)
                        writer.writerow(export_row)
            else:
                raise ValueError('export path not set.')
        except Exception as e:
            print(e)

    @classmethod
    def from_history_row_to_export_row(cls, history_row):
        export_row = {}
        for k, v in cls.export_file_meta_table.items():
            export_row[k] = history_row[v]
        for k in cls.export_file_headers:
            if k not in export_row:
                try:
                    cls.export_file_defaults[k]
                except KeyError:
                    raise Exception('field %s in not found in input or defaults'
                        % k)
        return export_row




 
class MockWSMessage(IncomingWSMessage):

    sanitizer_cls = None

    def translate(self, message):
        return message
