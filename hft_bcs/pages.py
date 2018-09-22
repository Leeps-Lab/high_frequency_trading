from ._builtin import Page, WaitPage
from .translator import system_start
from otree.api import Currency as c
from .models import Constants
from . import results
import logging
from django.core.cache import cache
from django.conf import settings


log = logging.getLogger(__name__)

class InformedConsent(Page):
    form_model = 'player'
    form_fields = ['consent']
    def is_displayed(self):
        is_first_round = (self.subsession.first_round == self.round_number)
        return is_first_round

class NoParticipation(Page):
    def is_displayed(self):
        consented = self.player.consent
        return not consented

class InstructionsFBA(Page):
    def is_displayed(self):
        consented = self.player.consent
        round_is_instructed = self.subsession.is_trial or (
            self.subsession.first_round == self.round_number)
        round_is_fba = True if self.subsession.design == 'FBA' else False
        return consented and round_is_instructed and round_is_fba

class InstructionsCDA(Page):
    def is_displayed(self):
        consented = self.player.consent
        round_is_instructed = self.subsession.is_trial or (
            self.subsession.first_round == self.round_number)
        round_is_cda = True if self.subsession.design == 'CDA' else False
        return consented and round_is_instructed and round_is_cda

class PreWaitPage(WaitPage):
    def is_displayed(self):
        consented = self.player.consent
        return consented

    def after_all_players_arrive(self):
        pass

class index(Page):
    def is_displayed(self):
        consented = self.player.consent
        return consented

round_results = {}
class ResultsWaitPage(WaitPage):
    def is_displayed(self):
        consented = self.player.consent
        return consented

    def after_all_players_arrive(self):
        subsession = self.subsession
        # take speed cost
        for player in self.group.get_players():
            player.take_cost()
            payoff_for_round = player.calc_payoff()
            if subsession.is_trial is False:
                if subsession.restore is True and (subsession.first_round == self.round_number):
                    subsession.restore_payoffs()
                player.participant.payoff += payoff_for_round
                if player.participant.vars['payoff_round'] == self.round_number:
                    player.participant.vars['round_payoff'] = payoff_for_round
        # process output to display
        session_log_file = self.subsession.log_file
        gid = self.group.id
        results_for_group = results.BCS_process(session_log_file, gid)
        round_results[gid] = results_for_group

class Results(Page):
    def is_displayed(self):
        consented = self.player.consent
        return consented

    def vars_for_template(self):
        gid = self.group.id
        return test[gid]

class SessionResults(Page):
    def is_displayed(self):
        round_is_final = self.round_number == self.subsession.last_round
        consented = self.player.consent
        return consented and round_is_final

    def vars_for_template(self):
        random_round_pay = self.session.config['random_round_payment']
        payoff_round = self.participant.vars['payoff_round']
        total_payoff = round(self.participant.payoff * 1e-4, 4)
        round_payoff = round(self.participant.vars['round_payoff'] * 1e-4, 4)
        out = {
            'random_round_pay': random_round_pay,
            'payoff_round': payoff_round, 
            'round_payoff': c(round_payoff),
            'total_payoff': c(total_payoff)
        }
        return out

page_sequence = [
    InformedConsent,
    NoParticipation,
    InstructionsCDA,
    InstructionsFBA,
    PreWaitPage,
    index,
    ResultsWaitPage,
    Results,
    SessionResults
]