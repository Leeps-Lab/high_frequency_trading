from .market_fact import *
import math
from hft.equations import price_grid
from itertools import count
import logging

log = logging.getLogger(__name__)

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
        self.transaction_counter = count(1, 1)
        self.sum_weights = 0
        self.discount_rate = round(
            self.k_reference_price * self.timer.session_duration, 2)

    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)
        new_price = kwargs['execution_price']
        n_transaction = next(self.transaction_counter)
        if n_transaction == 1:
            # recursive formula holds for n > 1
            # also for first transaction below is
            # obvious
            self.reference_price = new_price
        discount_multiplier = math.e **  - (
            self.timer.time_since_previous_step * self.discount_rate)
        self.sum_weights = 1 + self.sum_weights * discount_multiplier
        new_reference_price = price_grid(
            (new_price * (1 - self.sum_weights ** -1 ) + (
                self.reference_price * self.sum_weights ** -1)))
#        print('ref price', self.timer.time_since_previous_step, discount_multiplier, n_transaction, self.sum_weights, self.reference_price)
        if self.reference_price != new_reference_price:
            self.reference_price = new_reference_price
            self.has_changed = True
        else:
            self.has_changed = False


class SignedVolume(MarketFact):

    defaults = {'signed_volume': 0, 'k_signed_volume': 0}
    name = 'signed_volume'
    external_inputs = ('buy_sell_indicator', 'best_bid', 'best_offer', 'execution_price')
    is_time_aware = True


    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)
        price = kwargs['execution_price']
        best_offer = kwargs['best_offer']
        best_bid = kwargs['best_bid']
        if price == best_offer:
            offset = 0.5
        elif price == best_bid:
            offset = - 0.5
        else:
            log.debug('bad execution price %d' % price)
            return
        discount_multiplier = math.e ** (
             -1 * self.k_signed_volume * self.timer.time_since_previous_step)
        discounted_sig_vol = self.signed_volume * discount_multiplier
        new_signed_volume = round(offset + discounted_sig_vol, 2)
        if self.signed_volume != new_signed_volume:
            self.signed_volume = new_signed_volume
            self.has_changed = True
        else:
            self.has_changed = False
