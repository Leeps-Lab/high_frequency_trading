from ._builtin import Page, WaitPage
from .translator import system_start
from otree.api import Currency as c
from .models import Constants
from .utility import GroupResult, nanoseconds_since_midnight as labtime
from . import results
from django.core.cache import cache
from django.conf import settings


class PreWaitPage(WaitPage):
    pass

class index(Page):
    pass

class Instructions(Page):
    pass

test = {}
class ResultsWaitPage(WaitPage):
    def after_all_players_arrive(self):
        # take speed cost
        for player in self.group.get_players():
            player.take_cost()
            payoff_for_round = player.calc_payoff()
            player.participant.payoff += payoff_for_round
            if player.participant.vars['payoff_round'] == self.round_number:
                player.participant.vars['real_payoff'] = payoff_for_round
        # process output to display
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
    timeout_seconds = 10
    def vars_for_template(self):
        gid = self.group.id
        return test[gid]

class SessionResults(Page):
    def is_displayed(self):
        return self.round_number == Constants.num_rounds

    def vars_for_template(self):
        payoff_round = self.participant.vars['payoff_round']
        real_payoff = self.participant.vars['real_payoff']
        return {'payoff_round': c(payoff_round), 'real_payoff': c(real_payoff)}


page_sequence = [
    PreWaitPage,
    index,
    ResultsWaitPage,
    Results,
    SessionResults
]