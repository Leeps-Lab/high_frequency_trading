from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants
import random
from .translator import System_Start_Msg

class InitialWaitPage(WaitPage):

	def after_all_players_arrive(self):
		self.group.connect_to_exchange()


class PreWaitPage(WaitPage):
    def after_all_players_arrive(self):
        self.group.wake_investor_up()
        self.group.send_to_exchange(System_Start_Msg('S'))

class ResultsWaitPage(WaitPage):

	def after_all_players_arrive(self):
		self.group.disconnect_from_exchange()


class Results(Page):
    pass


class MessageSend(Page):
    form_model = 'player'
    form_fields = ['msg']

    def before_next_page(self):
        self.group.send_message(random.choice(['U', 'O', 'X']))

class Start(Page):
    pass
        


page_sequence = [
    PreWaitPage,
    Start,
]
