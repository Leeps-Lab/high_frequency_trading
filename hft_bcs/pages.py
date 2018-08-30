from ._builtin import Page, WaitPage
from .translator import system_start
from .models import Constants
from .utility import GroupResult, nanoseconds_since_midnight as labtime
from . import results
from django.core.cache import cache
from django.conf import settings


class PreWaitPage(WaitPage):
    pass

class index(Page):
    pass


test = {}
class ResultsWaitPage(WaitPage):
    def after_all_players_arrive(self):
        session_logs = self.subsession.log_file
        session_events = results.MarketEvents.init_many(session_logs)
        gid = self.group.id
        for market in session_events:
            if market.group == str(gid):
                test[gid] = {}
                m = results.BCSMarket(market)
                m.process()
                profit, duration = results.BCS_results(m)
        test[gid]['profit'] = GroupResult(profit)
        test[gid]['duration'] = GroupResult(duration)

class Results(Page):
    def vars_for_template(self):
        gid = self.group.id
        return test[gid]

page_sequence = [
    PreWaitPage,
    index,
    ResultsWaitPage,
    Results
]