from collections import deque

max_offer = 2147483647
min_bid = 0



class TraderMarketPricePair:

    required_inputs = ()
    update_events = ()


    def __init__(self):
        self.bid = deque([min_bid], maxlen=2)
        self.offer = deque([max_offer], maxlen=2)
        self.bid_has_changed = False
        self.offer_has_changed = False
    
    def update(self, update_bid=True, update_offer=True, **kwargs):
        for k in self.required_inputs:
            if k not in kwargs:
                raise KeyError('input %s is missing in  %s' % (k, kwargs))
        previous_bid, previous_offer = self.get_position()
        if update_bid:
            self.calculate_bid(**kwargs)
        if update_offer:
            self.calculate_offer(**kwargs)
        self.validate(**kwargs)
        current_bid, current_offer = self.get_position()
        if previous_bid != current_bid:
            self.bid_has_changed = True
        if previous_offer != current_offer:
            self.offer_has_changed = True
    
    def calculate_bid(self, *args, **kwargs):
        raise NotImplementedError()

    def calculate_offer(self, *args, **kwars):
        raise NotImplementedError()

    def validate(self, *args, **kwargs):
        pass

    def get_position(self):
        return (self.bid, self.offer)


class ELOManualTraderPrice(TraderMarketPricePair):

    required_inputs = ('price', 'buy_sell_indicator')


    def validate(self, *args, **kwargs):
        


