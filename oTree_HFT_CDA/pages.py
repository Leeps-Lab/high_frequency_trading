from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .translator import System_Start_Msg
from .models import Constants
import random


class PreWaitPage(WaitPage):
    def after_all_players_arrive(self):
        self.group.connect_to_exchange()
        self.group.send_message_nondelay(System_Start_Msg('S'))
        self.group.spawn(Constants.inv_py, Constants.inv_url, Constants.inv_csv)
        self.group.spawn(Constants.jump_py, Constants.jump_url, Constants.jump_csv)
        

class Start(Page):
    pass

class ResultsWaitPage(WaitPage):

	def after_all_players_arrive(self):
		self.group.disconnect_from_exchange()


class Results(Page):
    pass



page_sequence = [
    PreWaitPage,
    Start,
    ResultsWaitPage,
]
