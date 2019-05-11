from collections import deque
import os
import csv


class RandomOrderSet:

    def __init__(self, column_headers, orders=None):
        self.column_headers = column_headers
        self.orders = orders

    @classmethod
    def from_csv(cls, source_path):
        if source_path is not None:
            with open(source_path, 'r') as csvfile:
                orders_raw = csv.reader(csvfile)
                meta = next(orders_raw) # first line is the header
                orders_stack = deque()
                for row in orders_raw:
                    orders_stack.append(row)
        else: 
            raise ValueError('source path is none.')
        return cls(meta, orders=orders_stack)
    
    def __iter__(self):
        return iter(self.orders)
    
    def __next__(self):
        if len(self.orders):
            order = self.orders.popleft()
            return {self.column_headers[ix]: field 
                        for ix, field in enumerate(order)}
        else:
            raise StopIteration()
    
    def __bool__(self):
        return True if len(self.orders) else False


if __name__ == '__main__':
    source_file_path = 'test_orders.csv'
    random_order_set = RandomOrderSet.from_csv(source_file_path)
    while random_order_set:
        next_order = next(random_order_set)
        print(next_order)

