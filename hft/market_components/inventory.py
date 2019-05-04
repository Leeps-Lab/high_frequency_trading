from math import ceil

class Inventory:

    default_ticker = 'LEEPZ'

    def __init__(self, ticker=default_ticker, cash=0):
        self.__ticker = ticker
        self.__units = 0
        self.__cash = cash
        self.__cost = 0

    @property
    def ticker(self):
        return self.__ticker

    @property
    def cash(self):
        return self.__cash

    @property
    def cost(self):
        return self.__cost
    
    def position(self):
        return self.__units

    def add(self):
        self.__units += 1
    
    def remove(self):
        self.__units += -1

    def valuate(self, reference_price):
        return ceil(reference_price * self.__units)

    def liquidify(self, liquidation_price, discount_rate=0):
        shares_value = ceil(liquidation_price * self.__units)
        discounted_amount = ceil(discount_rate * shares_value)
        self.__cash += shares_value - discounted_amount
        self.__cost += discounted_amount
        self.__units -= self.__units

if __name__ == '__main__':
    inv = Inventory(cash=100)
    inv.add()
    inv.add()
    inv.remove()
    inv.liquidify(5, discount_rate=0.1)
    print(inv.cash)

        