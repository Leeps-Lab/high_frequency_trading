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

def latent_bid_and_offer(
        focal_best_bid, focal_best_offer, focal_signed_volume, ext_best_bid, 
        ext_best_offer, ext_signed_volume, inventory_position, sliders, 
        halftick=1e4 * 0.5):
    latent_bid = price_grid(
        sliders['slider_a_z'] * (
            ext_best_bid + halftick * sliders['slider_a_x'] * ext_signed_volume) + (
            1 - sliders['slider_a_z']) * (
            focal_best_bid + halftick * sliders['slider_a_x'] * focal_signed_volume) - (
            halftick * sliders['slider_a_y'] * inventory_position)
    )
    latent_offer = price_grid(
        sliders['slider_a_z'] * (
         ext_best_offer + halftick * sliders['slider_a_x'] * ext_signed_volume) + (
         1 - sliders['slider_a_z']) * (
         focal_best_offer + halftick * sliders['slider_a_x'] * focal_signed_volume) - (
         halftick * sliders['slider_a_y'] * inventory_position)
    )
    return (latent_bid, latent_offer)