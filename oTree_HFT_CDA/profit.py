class Price_Node:
    def __init__(self, timestamp, fp):
        self.timestamp = timestamp
        self.fp = fp


class Price_Log:
    def __init__(self, length, fundamental_price):
        self.list = []
        self.size = 0
        self.length = length                    
        self.push(0, fundamental_price)                     

    def push(self, time, price):
        self.list.append(Price_Node(time, price))
        self.size += 1
        self.popBackOff()

    def popBackOff(self):
        if self.size > self.length:
            self.list.pop(0)

    def getFP(self, timestamp):
        for priceNode in reversed(self.list):
            if priceNode.timestamp <= timestamp:
                print(priceNode.fp)
                return priceNode.fp

