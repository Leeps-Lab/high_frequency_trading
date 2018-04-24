from .exchange_socket import Exchange_Socket
from .translator import *
import numpy as np

try:
    import thread
except ImportError:
    import _thread as thread
import time

from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)

author = 'Your name here'

doc = """
Your app description
"""


class Constants(BaseConstants):
    name_in_url = 'otree_HFT_CDA'
    players_per_group = None
    num_rounds = 5
    exchange_soc = Exchange_Socket()
    # Test with lab exchange
    exchange_soc.connect("127.0.0.1", 12001)
    # Test sendng of system start message
        # exchange_soc.send(System_Event_Msg("S"))
    


class Subsession(BaseSubsession):

    # Guarantees 'counter' will be in session.vars
    def creating_session(self):
        if 'counter' not in self.session.vars:
            self.session.vars['counters'] = 1

    # increases the counter
    def counter_increasing(self):
        self.session.vars['counters'] += 1

    # Returns current counter
    def get_counter(self):
        return self.session.vars['counters']

    # Returns current counter then increases counter
    def get_increase(self):
        prev_counter = self.session.vars['counters']
        self.counter_increasing()
        return prev_counter



class Group(BaseGroup):
    def send_message(self):
        for player in self.get_players():
            player.send_message()


class Player(BasePlayer):
    msg = models.StringField()

    #Buy Price Information From MessageSend.html
    buy_computer_num = models.StringField()
    buy_price = models.IntegerField()
    buy_immediate = models.BooleanField()

    # Sell Price Information MessageSend.html
    sell_computer_num = models.StringField()
    sell_price = models.IntegerField()
    sell_immediate = models.BooleanField()

    # Maker Price Information MessageSend.html
    maker_computer_num = models.StringField()
    maker_price = models.IntegerField()
    maker_spread = models.IntegerField()

    # Cancel Price Information MessageSend.html
    cancel_order_num = models.StringField()

    # Replace Price Information MessageSend.html
    replaced_order_token = models.StringField()
    replace_computer_num = models.StringField()
    replace_buy_or_sell = models.StringField()
    replace_price = models.IntegerField()

    def send_message(self):
        if self.msg == "buy":
            buy_message = Enter_Order_Msg(self.buy_computer_num,"EBUY",self.subsession.get_increase(),self.buy_price*1000,0)
            Constants.exchange_soc.send(buy_message)
        elif self.msg == "sell":
            sell_message = Enter_Order_Msg(self.sell_computer_num, "ESELL",self.subsession.get_increase() , self.sell_price*1000, 0)
        elif self.msg == "maker":
            maker_message_buy = Enter_Order_Msg(self.buy_computer_num,"EBUY",self.subsession.get_increase(),(self.buy_price - self.maker_spread)*1000,0)
            maker_message_sell = Enter_Order_Msg(self.buy_computer_num,"ESELL",self.subsession.get_increase(),(self.buy_price + self.maker_spread)*1000,0)
        elif self.msg == "cancel":
            cancel_message = Cancel_Order_Msg(self.cancel_order_num)
        elif self.msg == "replace":
            buy_or_sell = None
            if self.replace_buy_or_sell == "buy":
                buy_or_sell = "UBUY"
            elif self.replace_buy_or_sell == "sell":
                buy_or_sell = "USELL"

            replace_message = Replace_Order_Msg(self.replaced_order_token, self.replace_computer_num, buy_or_sell, self.subsession.get_increase(), self.replace_price, 0)


            # print(replace_message,"This is a replace OuchMessage")

