from ._builtin import Page, WaitPage
from otree.api import Currency as c
from .models import Constants
import logging
from django.core.cache import cache
from django.conf import settings
from .output import close_trade_session
from .cache import get_cache_key
from django.core.cache import cache

log = logging.getLogger(__name__)

# this module is under construction
# we will update this once we finish
# building the new environment components
 

class PreWaitPage(WaitPage):
    def after_all_players_arrive(self):
        pass

class index(Page):
    pass


class leeps(Page):
    pass


class ResultsWaitPage(WaitPage):

    def after_all_players_arrive(self):
        trade_session_id = self.session.vars['trade_sessions'][self.subsession.id]
        ts_key = get_cache_key(trade_session_id, 'trade_session')
        trade_session = cache.get(ts_key)
        close_trade_session(trade_session)
        

class Results(Page):
    pass


page_sequence = [
    PreWaitPage,
    leeps,
    ResultsWaitPage,
    Results,
]