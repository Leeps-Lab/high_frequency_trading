import sys
import csv
from collections import namedtuple
import matplotlib.pyplot as plt

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


def mainPlot(investor_arrivals_file_name, external_feed_file_name):

    Order = namedtuple('Order', ['arrival_time', 'market_id_in_subsession', 'price', 'buy_sell_indicator', 'time_in_force', 'fundamental_value'])

    with open(investor_arrivals_file_name, 'r') as f:
        arrivals = [
            Order(
                float(o['arrival_time']),
                int(o['market_id_in_subsession']),
                int(o['price']),
                o['buy_sell_indicator'],
                float(o['time_in_force']),
                float(o['fundamental_value']),
            )
            for o in csv.DictReader(f)
        ]

    bids = set()
    asks = set()

    orderHistory = []
    
    i = 0
    while i < len(arrivals):
        cur_time = arrivals[i].arrival_time

        # batch arrivals that occur in the same second
        cur_arrivals = []
        while i < len(arrivals) and arrivals[i].arrival_time == cur_time:
            cur_arrivals.append(arrivals[i])
            i += 1

        # clear expired orders
        #bids = set(filter(lambda order: order.arrival_time + order.time_in_force > cur_time, bids))
        #asks = set(filter(lambda order: order.arrival_time + order.time_in_force > cur_time, asks))

        for order in bids.copy():
            if order.arrival_time + order.time_in_force <= cur_time:
                bids.remove(order)
                orderHistory.append({
                    'price': order.price, 
                    'arrivalTime': order.arrival_time, 
                    'exitTime': order.arrival_time + order.time_in_force,
                    'isBid' : True
                })

        for order in asks.copy():
            if order.arrival_time + order.time_in_force <= cur_time:
                asks.remove(order)
                orderHistory.append({
                    'price': order.price, 
                    'arrivalTime': order.arrival_time, 
                    'exitTime': order.arrival_time + order.time_in_force,
                    'isBid' : False
                })
            
        # process new order arrivals
        for order in cur_arrivals:
            if order.buy_sell_indicator == 'B':
                # calc best ask and check whether new order crosses
                best_ask = min(asks, key=lambda order: order.price) if asks else None
                if best_ask is not None and order.price > best_ask.price:
                    asks.remove(best_ask)
                    orderHistory.append({
                        'price': best_ask.price, 
                        'arrivalTime': best_ask.arrival_time, 
                        'exitTime': cur_time,
                        'isBid': False
                    })
                    orderHistory.append({
                        'price': order.price, 
                        'arrivalTime': order.arrival_time, 
                        'exitTime': order.arrival_time,
                        'isBid': True
                    })
                else:
                    bids.add(order)
            
            else:
                best_bid = max(bids, key=lambda order: order.price) if bids else None
                if best_bid is not None and order.price < best_bid.price:
                    bids.remove(best_bid)
                    orderHistory.append({
                        'price': best_bid.price, 
                        'arrivalTime': best_bid.arrival_time, 
                        'exitTime': cur_time,
                        'isBid': True
                    })
                    orderHistory.append({
                        'price': order.price, 
                        'arrivalTime': order.arrival_time, 
                        'exitTime': order.arrival_time,
                        'isBid': False
                    })
                else:
                    asks.add(order)

    for order in bids:
        orderHistory.append({
            'price': order.price, 
            'arrivalTime': order.arrival_time, 
            'exitTime': order.arrival_time + order.time_in_force,
            'isBid' : True
        })

    for order in asks:
        orderHistory.append({
            'price': order.price, 
            'arrivalTime': order.arrival_time, 
            'exitTime': order.arrival_time + order.time_in_force,
            'isBid' : False
        })

    orderHistory.sort(key = lambda order: order['arrivalTime'])

    #plt.hlines(y = orderHistory['price'], )
    graphData = {
        k: [order[k] for order in orderHistory]
        for k in orderHistory[0].keys()
    }
    print(graphData)

'''
if __name__ == '__main__':
    main()
'''
