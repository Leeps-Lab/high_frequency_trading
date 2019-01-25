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


max_ask = 2147483647
min_bid = 0

def price_grid(price, gridsize=1e4):
    """
    the grid
    """
    price_in_range = price
    if price < min_bid:
        price_in_range = min_bid
    elif price > max_ask:
        price_in_range = max_ask
    grid_formula = round((price_in_range - min_bid) / gridsize)
    grid_price = int(grid_formula * gridsize)
    return grid_price

class OrderImbalance:
    def __init__(self):
        self.order_imbalance = 0
        self.latest_execution_time = None
    def step(self, buy_sell_indicator, constant=1):
        now = time.time()
        if self.latest_execution_time is None:
            self.latest_execution_time = now 
        time_since_last_execution = now - self.latest_execution_time
        offset = -1 if buy_sell_indicator == 'B' else 1
        order_imbalance = (
            offset + self.order_imbalance * math.e ** (-1 * constant * time_since_last_execution) 
        )
        self.latest_execution_time = now
        self.order_imbalance = order_imbalance
        return order_imbalance   

# def order_imbalance_function(constant=1):
#     """
#     dan's order imbalance function
#     """   
#     order_imbalance = 0
#     while True: 
#         latest_execution_time = time.time()
#         buy_sell_indicator = yield order_imbalance
#         offset = -1 if buy_sell_indicator == 'B' else 1
#         time_since_last_execution = time.time() - latest_execution_time
#         order_imbalance = (
#             offset + order_imbalance * math.e ** (-1 * constant * time_since_last_execution) 
#         )

def bid_aggressiveness(b_x, b_y, x, y):
    """
    B(x(t), y(t))
    x: order imbalance
    y: inventory position
    """
    return - b_x * x + b_y * y

def sell_aggressiveness(a_x, a_y, x, y):
    """
    A(x(t), y(t))
    x: order imbalance
    y: inventory position
    """
    return a_x * x - a_y * y
 
def latent_bid(bb, S, bid_aggressiveness):
    """
    LB(t)
    bb: best bid
    S: half a tick
    """
    return bb - S * bid_aggressiveness

def latent_offer(bo, S, bid_aggressiveness):
    """
    LB(t)
    bb: best offer
    S: half a tick
    """
    return bo + S * sell_aggressiveness

def latent_bid_and_offer(best_bid, best_offer, order_imbalance, inventory, sliders, S=1e4,
        bid_aggressiveness=bid_aggressiveness, sell_aggressiveness=sell_aggressiveness):
    b = bid_aggressiveness(sliders.a_x, sliders.a_y, order_imbalance, inventory)
    a = sell_aggressiveness(sliders.a_x, sliders.a_y, order_imbalance, inventory)
    latent_bid = best_bid - 0.5 * S * b
    latent_ask = best_offer + 0.5 * S * a
    return price_grid(latent_bid), price_grid(latent_ask)