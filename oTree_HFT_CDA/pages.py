from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants


class MyPage(Page):
    pass


class ResultsWaitPage(WaitPage):
    pass

class Results(Page):
    pass

class MessageSend(Page):
	form_model = 'player'
	form_fields = ['msg', 'buy_computer_num', 'buy_price',
                   'sell_computer_num', 'sell_price',
                   'maker_computer_num', 'maker_price', 'maker_spread',
                   'cancel_order_num',
                   'replaced_order_token', 'replace_computer_num', 'replace_buy_or_sell', 'replace_price']

page_sequence = [
    start,
]
