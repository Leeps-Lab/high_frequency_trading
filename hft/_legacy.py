            
            
# class BCSMaker(BCSTrader):

#     def calc_price(self, buy_sell_indicator):
#         """
#         return order price for a maker order based on spread
#         """
#         leg_length = int(self.spread / 2)
#         multiplier = -1 if buy_sell_indicator == 'B' else 1
#         price = int(self.fp + multiplier * leg_length)
#         return price

#     def first_move(self, **kwargs):
#         self.role = self.__class__.__name__
#         delay = self.calc_delay()
#         for side in ('B', 'S'):
#             price = self.calc_price(side)
#             order_info = self.orderstore.enter(price=price, buy_sell_indicator=side, 
#                             time_in_force=99999)
#             host, port = self.exchange_host, self.exchange_port
#             message_content = {'host': host, 'port': port, 'type': 'enter', 'delay':
#                 delay, 'order_info': order_info}
#             internal_message = format_message('exchange', **message_content)
#             self.outgoing_messages.append(internal_message)

#     def jump(self, **kwargs):
#         """
#         assumes trader has active/pending orders in market
#         reprice orders
#         replace sell order first if jump is positive
#         """
#         is_positive_jump = super().jump(**kwargs)
#         # get list of active or pending orders
#         self.makers_reprice(start_from_above=is_positive_jump)

#     def makers_reprice(self, start_from_above=True):
#         orders = self.orderstore.all_orders()
#         assert len(orders) <= 2, 'more than two orders in market: %s' % self.orderstore
#         sorted_orders = sorted(orders, key=lambda order: order['price'], 
#                             reverse=start_from_above)
#         delay = self.calc_delay()
#         for o in sorted_orders:
#             token, buy_sell_indicator = o['order_token'], o['buy_sell_indicator']
#             new_price = self.calc_price(buy_sell_indicator)
#             order_info = self.orderstore.register_replace(token, new_price)
#             host, port = self.exchange_host, self.exchange_port
#             message_content = {'host': host, 'port': port, 'type': 'replace', 'delay':
#                 delay, 'order_info': order_info}
#             internal_message = format_message('exchange', **message_content)
#             self.outgoing_messages.append(internal_message)

#     def spread_change(self, **kwargs):
#         new_spread = int(kwargs['spread'])
#         self.spread = new_spread
#         self.makers_reprice()

        
    # def maker_broadcast_info(self, order_token):
    #     low_leg, high_leg = int(self.fp - self.spread / 2), int(self.fp + self.spread / 2)
    #     message_content = { 'group_id': self.market_id, 'type': 'maker_confirm', 
    #         'message': { 'leg_up': high_leg, 'leg_down': low_leg, 'order_token': order_token, 
    #             'id': self.id_in_group }}
    #     internal_message = format_message('broadcast', **message_content)     
    #     return internal_message

    # def accepted(self, **kwargs):
    #     super().accepted(**kwargs)
    #     order_token = kwargs['order_token']
    #     broadcast_info = self.maker_broadcast_info(order_token)
    #     message_content = {}
    #     self.outgoing_messages.append(broadcast_info)

    # def replaced(self, **kwargs):
    #     super().replaced(**kwargs)  
    #     order_token = kwargs['replacement_order_token']
    #     broadcast_info = self.maker_broadcast_info(order_token)
    #     self.outgoing_messages.append(broadcast_info)

    # def executed(self, **kwargs):
    #     order_info = super().executed(**kwargs)
    #     time_in_force = order_info['time_in_force']
    #     side = order_info['buy_sell_indicator']
    #     # make sure it is not a sniper order.
    #     if time_in_force != 0:
    #         host, port = self.exchange_host, self.exchange_port
    #         price = self.calc_price(side)
    #         delay = self.calc_delay()
    #         order_info = self.orderstore.enter(price=price, buy_sell_indicator=side, 
    #                         time_in_force=99999)
    #         message_content = {'host': host, 'port': port, 'type': 'enter', 'delay':
    #             delay, 'order_info': order_info}
    #         internal_message = format_message('exchange', **message_content)
    #         self.outgoing_messages.append(internal_message)
    

# class BCSOut(BCSTrader):

#     def first_move(self, **kwargs):
#         self.role = self.__class__.__name__
#         self.leave_market()
#         message_content = { 'group_id': self.market_id, 'type': 'leave_market', 
#             'message': {'id': self.id_in_group }}
#         internal_message = format_message('broadcast', **message_content)    
#         self.outgoing_messages.append(internal_message)

# class BCSSniper(BCSOut):

#     def jump(self, **kwargs):
#         is_positive_jump = super().jump(**kwargs)
#         side = 'B' if is_positive_jump else 'S'
#         host, port = self.exchange_host, self.exchange_port
#         order_info = self.orderstore.enter(price=self.fp, buy_sell_indicator=side, 
#                             time_in_force=0)
#         delay = self.calc_delay()
#         message_content = {'host': host, 'port': port, 'type': 'enter', 'delay':
#                 delay, 'order_info': order_info}
#         internal_message = format_message('exchange', **message_content)
#         self.outgoing_messages.append(internal_message)

# class BCSInvestor(BCSOut):

#     def invest(self, **kwargs):
#         host, port = self.exchange_host, self.exchange_port
#         order_side = kwargs['side']
#         price = 2147483647  if order_side == 'B' else 0
#         order_info = self.orderstore.enter(price=price, buy_sell_indicator=order_side, 
#                                     time_in_force=0)
#         message_content = {'host': host, 'port': port, 'type': 'enter', 'delay':
#                 0., 'order_info': order_info}
#         internal_message = format_message('exchange', **message_content)
#         self.outgoing_messages.append(internal_message)