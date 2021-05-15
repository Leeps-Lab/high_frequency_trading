from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants
import math
import time
from AnonPay.pages import formatNicely


class Consent(Page):
    form_model = 'player'
    form_fields = ['consent']
    timeout_submission = {'consent': False}
    timeout_seconds = 60

    def vars_for_template(self):
        return {'consent_timeout_min': math.ceil(self.timeout_seconds / 60)}
    
    def is_displayed(self):
        return self.round_number == 1

    def before_next_page(self):
        self.participant.vars['payment'] = self.session.config['participation_fee']

        if self.timeout_happened:
            self.player.consent = False
            self.player.participant.vars['consent'] = False
        else:
            self.player.participant.vars['consent'] = self.player.consent
    
class BlockDropouts(Page):
    def is_displayed(self):
        return self.round_number == 1 and self.player.consent == False

page_sequence = [Consent, BlockDropouts]
