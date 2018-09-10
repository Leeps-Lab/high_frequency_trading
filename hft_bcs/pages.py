from ._builtin import Page, WaitPage
from .translator import system_start
from otree.api import Currency as c
from .models import Constants
from . import results
import logging
from django.core.cache import cache
from django.conf import settings


log = logging.getLogger(__name__)

class InstructionsFBA(Page):
    def is_displayed(self):
        is_instructed = self.subsession.is_trial or (self.subsession.first_round == self.round_number)
        is_fba = True if self.subsession.design == 'FBA' else False
        return is_instructed and is_fba

class InstructionsCDA(Page):
    def is_displayed(self):
        is_instructed = self.subsession.is_trial or (self.subsession.first_round == self.round_number)
        is_cda = True if self.subsession.design == 'CDA' else False
        return is_instructed and is_cda

class PreWaitPage(WaitPage):
    def after_all_players_arrive(self):
        pass

class index(Page):
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
        session_log_file = self.subsession.log_file
        gid = self.group.id
        results_for_group = results.BCS_process(session_log_file, gid)
        test[gid] = results_for_group

class Results(Page):
    def vars_for_template(self):
        gid = self.group.id
        return test[gid]

class SessionResults(Page):
    def is_displayed(self):
        return self.round_number == self.subsession.last_round

    def vars_for_template(self):
        payoff_round = self.participant.vars['payoff_round']
        total_payoff = round(self.participant.payoff * 1e-4, 4)
        real_payoff = round(self.participant.vars['real_payoff'] * 1e-4, 4)
        out = {
            'payoff_round': payoff_round, 
            'real_payoff': c(real_payoff),
            'total_payoff': c(total_payoff)
        }
        return out


page_sequence = [
    InstructionsCDA,
    InstructionsFBA,
    PreWaitPage,
    index,
    ResultsWaitPage,
    Results,
    SessionResults
]