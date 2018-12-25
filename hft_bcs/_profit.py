# revised for pep-8
# august 4th 2018
# TODO: implement __format__

class Price_Node:
    def __init__(self, timestamp, fp):
        self.timestamp = timestamp
        self.fp = fp


class Price_Log:
    def __init__(self, length, fundamental_price):
        self.prices = []
        self.size = 0
        self.length = length                    
        self.push(0, fundamental_price)                     

    def push(self, time, price):
        self.prices.append(Price_Node(time, price))
        self.size += 1
        self.pop_back_off()

    def pop_back_off(self):
        if self.size > self.length:
            self.prices.pop(0)

    def get_FP(self, timestamp):
        for price_node in reversed(self.prices):
            if price_node.timestamp <= timestamp:
                return price_node.fp

    def __str__(self):
        return str(self.prices)


