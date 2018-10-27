from ._builtin import Page, WaitPage
from .translator import system_start
from otree.api import Currency as c
from .models import Constants
from .payoffs import SessionPayoff
from . import results
import logging
from django.core.cache import cache
from django.conf import settings


log = logging.getLogger(__name__)

class InformedConsent(Page):
    form_model = 'player'
    form_fields = ['consent']
    def is_displayed(self):
        is_first_round = self.round_number == 1
        return is_first_round

class NoParticipation(Page):
    def is_displayed(self):
        if self.round_number == 1:
            consented = self.player.consent
        else:
            # since you already consented in the first round
            consented = True
        return not consented

class InstructionsFBA(Page):
    def is_displayed(self):
        round_is_instructed = self.subsession.is_trial or (
            self.subsession.first_round == self.round_number)
        round_is_fba = True if self.subsession.design == 'FBA' else False
        return round_is_instructed and round_is_fba

class InstructionsCDA(Page):
    def is_displayed(self):
        round_is_instructed = self.subsession.is_trial or (
            self.subsession.first_round == self.round_number)
        round_is_cda = True if self.subsession.design == 'CDA' else False
        return round_is_instructed and round_is_cda

class PreWaitPage(WaitPage):
    def after_all_players_arrive(self):
        pass

class index(Page):
    pass

round_results = {}
class ResultsWaitPage(WaitPage):

    def after_all_players_arrive(self):
        subsession = self.subsession
        # take speed cost
        for player in self.group.get_players():
            player.take_cost()
            payoff_for_round = player.do_payoff()
            print('payoff for round', payoff_for_round)
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
    def vars_for_template(self):
        gid = self.group.id
        return round_results[gid]

class SessionEnd(WaitPage):
    """
    i really dont like participant.payoff
    there is some implicit stuff
    maybe just never use it till i have to
    """
    def is_displayed(self):
        round_is_final = self.round_number == self.subsession.last_round
        return round_is_final

    def after_all_players_arrive(self):
        for player in self.group.get_players():
            session_payoff = SessionPayoff(player)
            random_round_pay = self.session.config['random_round_payment']
            if random_round_pay:
                    _, payoff = session_payoff.random_round_payoff()  
            else:
                payoff = session_payoff.average_payoff()
            player.total_payoff = float(player.participant.payoff)
            fx = 1 / self.session.config['real_world_currency_per_point']
            player.participant.payoff = fx * payoff * 1 / Constants.conversion_factor

class SessionResults(Page):
    def is_displayed(self):
        round_is_final = self.round_number == self.subsession.last_round
        return round_is_final

    def vars_for_template(self):
        random_round_pay = self.session.config['random_round_payment']
        out = {'payoff_round': False}
        if random_round_pay:
            payoff_round = self.player.participant.vars['payoff_round']
            out = {'payoff_round': payoff_round}
        points_payoff = self.player.total_payoff * 1 / Constants.conversion_factor / self.subsession.total_rounds
        payoff_plus_participation = self.player.participant.payoff + self.session.config['participation_fee']
        points_payoff = SessionPayoff.round(points_payoff)  
        out['payoff'] = points_payoff
        out['payoff_plus_participation'] = payoff_plus_participation
        return out

page_sequence = [
    # InformedConsent,
    # NoParticipation,
    # InstructionsCDA,
    # InstructionsFBA,
    PreWaitPage,
    index,
    ResultsWaitPage,
    Results,
    SessionEnd,
    SessionResults
]