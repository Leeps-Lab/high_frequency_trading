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

from .models import GRIDSIZE

max_ask = 2147483647
min_bid = 0

def price_grid(price, gridsize=GRIDSIZE):
    """
    the grid
    """
    price_in_range = price
    if price < min_bid:
        price_in_range = min_bid
    elif price > max_ask:
        price_in_range = max_ask
    grid_price = math.floor((price_in_range - min_bid) / gridsize)
    return grid_price

def order_imbalance_function(constant=1):
    """
    dan's order imbalance function
    """   
    order_imbalance = 0
    while True: 
        latest_execution_time = time.time()
        buy_sell_indicator = yield order_imbalance
        offset = -1 if buy_sell_indicator == 'B' else 1
        time_since_last_execution = time.time() - latest_execution_time
        order_imbalance = (
            offset + order_imbalance * math.e ** (-1 * constant * time_since_last_execution) 
        )
            
def latent_bid_and_offer(best_bid, best_offer, order_imbalance, inventory, sliders,
        gridsize=GRIDSIZE):
        bid_aggresiveness = sliders.a_x *  order_imbalance - sliders.a_y * inventory
        sell_aggressiveness = - sliders.b_x * order_imbalance + sliders.b_y * inventory
        latent_bid = price_grid(best_bid - gridsize * bid_aggresiveness, gridsize)
        latent_ask = price_grid(best_offer + gridsize * sell_aggressiveness, gridsize)
        return (latent_bid, latent_ask)