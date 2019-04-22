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


# class OrderImbalance:

#     def __init__(self, discount_constant):
#         self.order_imbalance = 0
#         self.latest_execution_time = None
#         self.discount_constant = discount_constant

#     def start(self):
#         self.latest_execution_time = time.time()

#     def step(self, execution_price, best_bid, best_offer, buy_sell_indicator):
#         now = time.time()
#         if self.latest_execution_time is None:
#             self.latest_execution_time = now 
#         time_since_last_execution = now - self.latest_execution_time
#         if execution_price == best_bid:
#             offset = - 0.5 
#         elif execution_price == best_offer:
#             offset = + 0.5
#         else:
#             log.exception('bad execution price: {}: best bid {}: best offer {}'.format(
#                 execution_price, best_bid, best_offer))
#             return self.order_imbalance
#         order_imbalance = round(
#             offset + self.order_imbalance *  math.e ** (-1 * self.discount_constant * time_since_last_execution) 
#         ,2)
#         # print('imbalance {} time since exec {}: offset {}: {}'.format(order_imbalance,
#         #     time_since_last_execution, offset, new_exp))
#         self.latest_execution_time = now
#         self.order_imbalance = order_imbalance
#         return order_imbalance   


# class ReferencePrice:

#     def __init__(self, discount_constant):
#         self.discount_constant = discount_constant
#         self.reference_price = 0
#         self.session_start = None
#         self.session_duration = None

#     def start(self, session_duration=None):
#         if session_duration is not None:
#             self.session_duration = session_duration
#         if not isinstance(self.session_duration, int):
#             raise ValueError('invalid session duration {}:'.format(
#                 session_duration, session_duration.__class__.__name__))
#         self.session_start = time.time()
#         self.discount_rate = self.discount_constant / self.session_duration

#     def step(self, price):
#         time_elapsed_since_session_start = time.time() - self.session_start
#         weight_for_price = math.e ** (
#             (time_elapsed_since_session_start - self.session_duration) * self.discount_rate
#         )
#         new_reference_price = int((price * weight_for_price) + ((1 - weight_for_price) * self.reference_price))
#         self.reference_price = price_grid(new_reference_price)
#         return new_reference_price

# def bid_aggressiveness(b_x, b_y, x, y):
#     """
#     B(x(t), y(t))
#     x: order imbalance
#     y: inventory position
#     """
#     return b_x * x - b_y * y

# def sell_aggressiveness(a_x, a_y, x, y):
#     """
#     A(x(t), y(t))
#     x: order imbalance
#     y: inventory position
#     """
#     return - a_x * x + a_y * y
 

# def latent_bid_and_offer(best_bid, best_offer, order_imbalance, inventory, sliders, ticksize=1e4,
#         bid_aggressiveness=bid_aggressiveness, sell_aggressiveness=sell_aggressiveness):
#     b = bid_aggressiveness(sliders.a_x, sliders.a_y, order_imbalance, inventory)
#     a = sell_aggressiveness(sliders.a_x, sliders.a_y, order_imbalance, inventory)
#     latent_bid = best_bid + 0.5 * ticksize * b
#     latent_ask = best_offer - 0.5 * ticksize * a
#     # print('a_x {} : a_y {} : order imbalance {} : inventory {} : latent_bid {} : latent_offer {} : bid agg {} : sell agg {}'.format(
#     #     sliders.a_x, sliders.a_y, order_imbalance, inventory, latent_bid, latent_ask, b, a))
#     return price_grid(latent_bid), price_grid(latent_ask)


def latent_bid_and_offer(
        focal_best_bid, focal_best_offer, focal_signed_volume, ext_best_bid, 
        ext_best_offer, ext_signed_volume, inventory_position, sliders, 
        halftick=1e4 * 0.5):
    latent_bid = (
        sliders.a_z * (
            ext_best_bid + halftick * sliders.a_x * ext_signed_volume) + (
            1 - sliders.a_z) * (
            focal_best_bid + halftick * sliders.a_x * focal_signed_volume) - (
            halftick * sliders.a_y * inventory_position)
    )
    latent_offer = (
        sliders.a_z * (
         ext_best_offer + halftick * sliders.a_x * ext_signed_volume) + (
         1 - sliders.a_z) * (
         focal_best_offer + halftick * sliders.a_x * focal_signed_volume) - (
         halftick * sliders.a_y * inventory_position)
    )
    return price_grid(latent_bid), price_grid(latent_offer)