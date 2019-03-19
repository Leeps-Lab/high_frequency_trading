"""
a_x, a_y, b_x, b_y sensitivity parameters adjusted via slider by player
"""

"""
the grid
i = 0, 1, ....., n
delta_h = i.h + p_0
p_i = [(p-p_0) / delta_h]
"""

import math
import time
import logging

log = logging.getLogger(__name__)

max_ask = 2147483647
min_bid = 0

def price_grid(price, gridsize=1e4):
    integer_price = int(price)
    if integer_price < min_bid:
        integer_price = min_bid
    elif integer_price > max_ask:
        integer_price = max_ask
    grid_formula = round((integer_price - min_bid) / gridsize)
    grid_price = int(grid_formula * gridsize)
    return grid_price


class OrderImbalance:

    def __init__(self):
        self.order_imbalance = 0
        self.latest_execution_time = None

    def step(self, execution_price, best_bid, best_offer, buy_sell_indicator, constant=0.01):
        now = time.time()
        if self.latest_execution_time is None:
            self.latest_execution_time = now 
        time_since_last_execution = now - self.latest_execution_time
        if execution_price == best_bid:
            offset = -0.5 
        elif execution_price == best_offer:
            offset = +0.5
        else:
            log.exception('bad execution price: {}: best bid {}: best offer {}'.format(
                execution_price, best_bid, best_offer))
            return self.order_imbalance
        order_imbalance = (
            offset + self.order_imbalance *  math.e ** (-1 * constant * time_since_last_execution) 
        )
        # print('imbalance {} time since exec {}: offset {}: {}'.format(order_imbalance,
        #     time_since_last_execution, offset, new_exp))
        self.latest_execution_time = now
        self.order_imbalance = order_imbalance
        return order_imbalance   


class ReferencePrice:

    def __init__(self, discount_constant):
        self.discount_constant = discount_constant
        self.reference_price = 0
        self.session_start = None
        self.session_duration = None

    def start(self, session_duration=None):
        if session_duration is not None:
            self.session_duration = session_duration
        if not isinstance(self.session_duration, int):
            raise ValueError('invalid session duration {}:'.format(
                session_duration, session_duration.__class__.__name__))
        self.session_start = time.time()
        self.discount_rate = self.discount_constant / self.session_duration

    def step(self, price):
        time_elapsed_since_session_start = time.time() - self.session_start
        weight_for_price = math.e ** (
            (time_elapsed_since_session_start - self.session_duration) * self.discount_rate
        )
        new_reference_price = int((price * weight_for_price) + ((1 - weight_for_price) * self.reference_price))
        self.reference_price = price_grid(new_reference_price)
        return new_reference_price

def bid_aggressiveness(b_x, b_y, x, y):
    """
    B(x(t), y(t))
    x: order imbalance
    y: inventory position
    """
    return b_x * x - b_y * y

def sell_aggressiveness(a_x, a_y, x, y):
    """
    A(x(t), y(t))
    x: order imbalance
    y: inventory position
    """
    return - a_x * x + a_y * y
 

def latent_bid_and_offer(best_bid, best_offer, order_imbalance, inventory, sliders, ticksize=1e4,
        bid_aggressiveness=bid_aggressiveness, sell_aggressiveness=sell_aggressiveness):
    b = bid_aggressiveness(sliders.a_x, sliders.a_y, order_imbalance, inventory)
    a = sell_aggressiveness(sliders.a_x, sliders.a_y, order_imbalance, inventory)
    latent_bid = best_bid + 0.5 * ticksize * b
    latent_ask = best_offer - 0.5 * ticksize * a
    # print('a_x {} : a_y {} : order imbalance {} : inventory {} : latent_bid {} : latent_offer {} : bid agg {} : sell agg {}'.format(
    #     sliders.a_x, sliders.a_y, order_imbalance, inventory, latent_bid, latent_ask, b, a))
    return price_grid(latent_bid), price_grid(latent_ask)