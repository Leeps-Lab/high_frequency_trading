
class LEEPSBasicMaker(LEEPSTrader):

    message_dispatch = { 'spread_change': 'spread_change', 'speed_change': 'speed_change',
        'role_change': 'first_move', 'A': 'accepted', 'U': 'replaced', 'C': 'canceled', 
        'E': 'executed', 'slider_change': 'slider_change',
        'bbo_change': 'bbo_update', 'order_by_arrow': 'trader_bid_offer_change', 
        }

    def __init__(self, subject_state):
        super().__init__(subject_state)

    def first_move(self, **kwargs):
        self.leave_market()
        self.switch_to_market_tracking_role(**kwargs)
        if self.distance_from_best_quote is None:
            self.distance_from_best_quote = {'B': None, 'S': None}

    def calc_price(self, buy_sell_indicator, d=None):
        if d is None:
            d = self.distance_from_best_quote[buy_sell_indicator]
        best_quote = self.best_quotes[buy_sell_indicator]
        if buy_sell_indicator == 'B':
            price = best_quote - d
        elif buy_sell_indicator == 'S':
            price = best_quote + d
        else:
            raise ValueError('invalid buy_sell_indicator %s' % buy_sell_indicator)
        print('price', price, 'dfbq', self.distance_from_best_quote)
        return price
    
    def executed(self, **kwargs):
        order_info = super().executed(**kwargs)
        buy_sell_indicator = order_info['buy_sell_indicator']
        price = self.calc_price(buy_sell_indicator)
        new_order_info = self.orderstore.enter(price=price, 
                buy_sell_indicator=buy_sell_indicator, time_in_force=99999)
        delay = self.calc_delay()
        internal_message = self.exchange_message_from_order_info(new_order_info, 
            delay,  'enter')
        self.outgoing_messages.append(internal_message)
 
    def trader_bid_offer_change(self, price=None, buy_sell_indicator=None, **kwargs):
        if buy_sell_indicator is None:
            buy_sell_indicator = kwargs['side']
        if price is None:
            price = price_grid(kwargs['price'])
        best_quote = self.best_quotes[buy_sell_indicator]
        if price == MIN_BID or price == MAX_ASK:
            return
        else:
            d = abs(best_quote - price)
            self.distance_from_best_quote[buy_sell_indicator] = d
            orders = self.orderstore.all_orders(direction=buy_sell_indicator)
            delay = self.calc_delay()
            if orders:
                for o in orders:
                    existing_token = o['order_token']
                    existing_buy_sell_indicator = o['buy_sell_indicator']
                    if buy_sell_indicator == existing_buy_sell_indicator:
                        order_info = self.orderstore.register_replace(existing_token, price)
                        internal_message = self.exchange_message_from_order_info(order_info,
                            delay, 'replace')
                        self.outgoing_messages.append(internal_message)
            else:
                order_info = self.orderstore.enter(price=price, 
                    buy_sell_indicator=buy_sell_indicator, time_in_force=99999)
                internal_message = self.exchange_message_from_order_info(order_info,
                    delay, 'enter')
                self.outgoing_messages.append(internal_message)

    def bbo_update(self, **kwargs):
        self.best_quote_volumes['B'] = kwargs['volume_at_best_bid']
        self.best_quote_volumes['S'] = kwargs['volume_at_best_ask']
        new_best_bid, new_best_offer = kwargs['best_bid'], kwargs['best_offer'] 
        if new_best_bid != self.best_quotes['B']:
            self.best_quotes['B'] = new_best_bid
            if self.distance_from_best_quote['B'] is not None and (new_best_bid !=
                self.orderstore.bid):
                price = new_best_bid - self.distance_from_best_quote['B']
                print(new_best_bid, self.distance_from_best_quote['B'])
                if new_best_bid > MIN_BID and price > 0:
                    self.trader_bid_offer_change(price=price, buy_sell_indicator='B')
        if new_best_offer != self.best_quotes['S']:
            self.best_quotes['S'] = new_best_offer
            if self.distance_from_best_quote['S'] is not None and (new_best_offer !=
                self.orderstore.offer):
                print(new_best_offer, self.distance_from_best_quote['S'])
                price = new_best_offer + self.distance_from_best_quote['S']
                if new_best_offer < MAX_ASK and price > 0:
                    self.trader_bid_offer_change(price=price, buy_sell_indicator='S')
