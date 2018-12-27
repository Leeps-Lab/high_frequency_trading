from collections import namedtuple

Order = namedtuple('EnterOrder', 'side price time_in_force sleep_time')

maker_orders = [
                Order(side=b'B', price=2147483647, time_in_force=9999, sleep_time=0),
]

investor_orders = [Order(side=b'S', price=0, time_in_force=9999, sleep_time=0),
                   Order(side=b'S', price=0, time_in_force=9999, sleep_time=0)]

test_case_orders = reversed(maker_orders + investor_orders)
