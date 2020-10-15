import sys
import csv
from collections import namedtuple

"""
This script generates an external feed csv config file for otree experiments
To use it, first use draw.py in the simulator to generate
an external investor arrival file. Use that as input to this file.

This script essentially runs an external market simulation.

We iterate over the session duration at the millisecond level.
At each millisecond, we:
- remove any order which time in force has expired
- add any order that just arrived
- compute the BBO
- check if the BBO crosses
    - delete the crossing orders
    - compute the new BBO
- check of the BBO differs from the previous BBO
    - add it to the list of exogenous events

"""
# input csv header
# arrival_time,market_id_in_subsession,price,buy_sell_indicator,time_in_force
# output csv header
# arrival_time,market_id_in_subsession,e_best_bid,e_best_offer,e_signed_volume


def main(investor_arrivals_file_name, external_feed_file_name):

    Order = namedtuple('Order', ['arrival_time', 'market_id_in_subsession', 'price', 'buy_sell_indicator', 'time_in_force'])

    with open(investor_arrivals_file_name, 'r') as f:
        arrivals = [
            Order(
                float(o['arrival_time']),
                int(o['market_id_in_subsession']),
                int(o['price']),
                o['buy_sell_indicator'],
                float(o['time_in_force']),
            )
            for o in csv.DictReader(f)
        ]

    bids = set()
    asks = set()

    cur_best_bid = None
    cur_best_ask = None

    bbos = []

    i = 0
    while i < len(arrivals):
        cur_time = arrivals[i].arrival_time

        # batch arrivals that occur in the same second
        cur_arrivals = []
        while i < len(arrivals) and arrivals[i].arrival_time == cur_time:
            cur_arrivals.append(arrivals[i])
            i += 1

        # clear expired orders
        bids = set(filter(lambda order: order.arrival_time + order.time_in_force > cur_time, bids))
        asks = set(filter(lambda order: order.arrival_time + order.time_in_force > cur_time, asks))
            
        # process new order arrivals
        for order in cur_arrivals:
            if order.buy_sell_indicator == 'B':
                # calc best ask and check whether new order crosses
                best_ask = min(asks, key=lambda order: order.price) if asks else None
                if best_ask is not None and order.price > best_ask.price:
                    asks.remove(best_ask)
                else:
                    bids.add(order)
            
            else:
                best_bid = max(bids, key=lambda order: order.price) if bids else None
                if best_bid is not None and order.price < best_bid.price:
                    bids.remove(best_bid)
                else:
                    asks.add(order)

        best_bid = max(bids, key=lambda order: order.price) if bids else None
        best_ask = min(asks, key=lambda order: order.price) if asks else None
        if best_bid != cur_best_bid or best_ask != cur_best_ask:
            cur_best_bid = best_bid
            cur_best_ask = best_ask

            bbos.append({
                'arrival_time': cur_time,
                'market_id_in_subsession': 1,
                'e_best_bid': best_bid.price if best_bid else 0,
                'e_best_ask': best_ask.price if best_ask else 0x7FFFFFFF,
                'e_signed_volume': 0,
            })
    
    with open(external_feed_file_name, 'w') as f:
        fieldnames = [
            'arrival_time',
            'market_id_in_subsession',
            'e_best_bid',
            'e_best_ask',
            'e_signed_volume',
        ]
        writer = csv.DictWriter(f, fieldnames)
        writer.writeheader()
        writer.writerows(bbos)

'''
if __name__ == '__main__':
    main()
'''
