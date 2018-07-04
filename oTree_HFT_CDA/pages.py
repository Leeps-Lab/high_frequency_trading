from ._builtin import Page, WaitPage
from .translator import system_start
from .models import Constants
from .utility import nanoseconds_since_midnight as labtime
from django.core.cache import cache


class PreWaitPage(WaitPage):
    def after_all_players_arrive(self):      
        self.group.connect_to_exchange()
        self.group.send_exchange(system_start('S'))
        self.group.spawn(Constants.inv_py, Constants.inv_url, Constants.inv_csv)
        self.group.spawn(Constants.jump_py, Constants.jump_url, Constants.jump_csv)
        self.subsession.start_time = labtime()
        

class Start(Page):
#    timeout_seconds = 45
    pass


class ResultsWaitPage(WaitPage):

    def after_all_players_arrive(self):
        self.group.disconnect_from_exchange()
        #  cache.clear()    #   this will go somewhere here dont forget

class Results(Page):
    pass

page_sequence = [
    PreWaitPage,
    Start,
    ResultsWaitPage,
    Results
]