from .market_fact import *
import math
from hft.equations import price_grid

max_offer = 2147483647
min_bid = 0


class BestBidOffer(MarketFact):

    defaults = {
        'best_bid': min_bid, 'best_offer': max_offer, 'volume_at_best_bid': 0,
        'volume_at_best_offer': 0, 'next_bid': min_bid, 'next_offer': max_offer}
    name = 'bbo'
    input_to_attr_map = { 
        'best_ask': 'best_offer', 'volume_at_best_ask': 'volume_at_best_offer',
        'next_ask': 'next_offer'}
    required_input_fields = ('best_bid', 'best_ask', 'volume_at_best_bid',
        'volume_at_best_ask', 'next_bid', 'next_ask')


class ELOExternalFeed(MarketFact):

    defaults = {
        'e_best_bid': min_bid, 'e_best_offer': max_offer, 'e_signed_volume': 0}
    name = 'external_feed'
    required_input_fields = ('e_best_bid', 'e_best_offer',  'e_signed_volume')


class ReferencePrice(MarketFact):

    defaults = {'reference_price': 0, 'k_reference_price': 0}
    name = 'reference_price'
    required_input_fields = ('execution_price', )
    is_time_aware = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.discount_rate = round(
            self.k_reference_price * self.timer.session_duration, 2)

    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)
        new_price = kwargs['execution_price']
        weight_for_price = math.e ** (
            (self.timer.time_elapsed - self.timer.session_duration) *
            self.discount_rate)
        new_reference_price = price_grid(
            (new_price * weight_for_price) + (
             (1 - weight_for_price) * self.reference_price))
        if self.reference_price != new_reference_price:
            self.reference_price = new_reference_price
            self.__has_changed = True
        else:
            self.__has_changed = False


class SignedVolume(MarketFact):

    defaults = {'signed_volume': 0, 'k_signed_volume': 0}
    name = 'signed_volume'
    external_inputs = ('buy_sell_indicator', 'best_bid', 'best_offer')
    is_time_aware = True


    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)
        # 4 character in order token is also buy_sell_indicator
        bsi = kwargs['order_token'][3]
        offset = 0.5 if bsi == 'S' else - 0.5
        new_signed_volume = round(
            offset + self.signed_volume * math.e ** (
             -1 * self.k_signed_volume * self.timer.time_since_previous_step), 2)
        if self.signed_volume != new_signed_volume:
            self.signed_volume = new_signed_volume
            self.__has_changed = True
        else:
            self.__has_changed = False
