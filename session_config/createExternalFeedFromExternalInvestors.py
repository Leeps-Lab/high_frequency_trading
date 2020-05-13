from sys import argv

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
MAX_ASK = 2**31 - 1
MIN_BID = 0


# remove all orders whose time in force + arrive time is less than current time
def remove_expired_orders(orders, i):
    def cond(order, i):
        return i < float(order[0]) * 1000 + float(order[4]) * 1000
    return [order for order in orders if cond(order, i)]

# move new arrivals from arrivals to orders if the arrival happens this ms
def add_new_arrivals(orders, arrivals, i):
    for order in arrivals:
        if float(order[0]) * 1000 == i:
            orders.append(order)
    arrivals = [o for o in arrivals if o not in orders]
    return orders, arrivals

# compute and return highest bid
def new_bb(orders):
    buys = [o for o in orders if o[3] == 'B']
    if len(buys) == 0:
        return MIN_BID, None
    buys = sorted(buys, reverse=True, key=lambda o: int(o[2]))
    bb_order = buys[0]
    bb = int(bb_order[2])
    return bb, bb_order

# compute and return lowest ask
def new_bo(orders):
    sells = [o for o in orders if o[3] == 'S']
    if len(sells) == 0:
        return MAX_ASK, None
    sells = sorted(sells, key=lambda o: int(o[2]))
    bo_order = sells[0]
    bo = int(bo_order[2])
    return bo, bo_order

def remove_bb_bo(orders, bb_order, bo_order):
    orders.remove(bb_order)
    orders.remove(bo_order)
    return orders

def add_bbo(bbos, bb, bo, i):
    i = str(round(i / 1000, 3))
    bb = str(bb)
    bo = str(bo)
    new_bbo = [i, 1, bb, bo, 'N/A']
    bbos.append(new_bbo)
    return bbos

def write_bbos(fname, bbos):
    header = ['arrival_time','market_id_in_subsession',
        'e_best_bid','e_best_offer','e_signed_volume']
    header = ','.join(header)
    bbos = [','.join(map(str, line)) for line in bbos]
    bbos = [header, *bbos]
    with open(fname, 'w') as f:
        for order in bbos:
            f.write(order + '\n')

def main():
    # read investor file from command line arg
    investor_arrivals_file = argv[1]

    # read investor files into list
    with open(investor_arrivals_file, 'r') as f:
        arrivals = f.readlines()

    # split each order into a list and get rid of header
    # 0: arrival time
    # 1: market id in subsession
    # 2: price
    # 3: buy/sell indicator {'B','S'}
    # 4: time in force
    arrivals = [order.split(',') for order in arrivals][1:]

    # get duration in seconds
    duration = arrivals[-1][0]
    #convert duration to milliseconds
    duration_ms = int(float(duration) * 1000)

    # define variables
    bb = MIN_BID
    bb_order = None
    bo = MAX_ASK
    bo_order = None
    prev_bb = MIN_BID
    prev_bo = MAX_ASK
    orders = []
    bbos = []

    for i in range(duration_ms):
        orders = remove_expired_orders(orders, i)
        orders, arrivals = add_new_arrivals(orders, arrivals, i)
        bb, bb_order = new_bb(orders)
        bo, bo_order = new_bo(orders)
        while bb_order is not None and bo_order is not None and bb >= bo:
            orders = remove_bb_bo(orders, bb_order, bo_order)
            bb, bb_order = new_bb(orders)
            bo, bo_order = new_bo(orders)
        if bb != prev_bb or bo != prev_bo:
            bbos = add_bbo(bbos, bb, bo, i)
            prev_bb = bb
            prev_bo = bo
    
    write_bbos(argv[2], bbos)

if __name__ == '__main__':
    main()

