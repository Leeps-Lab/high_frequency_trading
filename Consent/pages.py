from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants
import math
import time
import random
from AnonPay.pages import formatNicely


class Consent(Page):
    form_model = 'player'
    form_fields = ['consent']
    timeout_submission = {'consent': False}
    '''
    # Auto advance page
    def get_timeout_seconds(self):
        timeout = self.session.config['auto_advance']
        if timeout > 0:
            return timeout
    '''
    
    def is_displayed(self):
        return self.round_number == 1
    
    def before_next_page(self):
        self.participant.vars['payment'] = self.session.config['participation_fee']

        if self.timeout_happened:
            self.player.consent = False
            self.player.participant.vars['consent'] = False
        else:
            self.player.participant.vars['consent'] = self.player.consent

class ConsentWaitPage(WaitPage):
    def is_displayed(self):
        return self.round_number == 1
    
    def after_all_players_arrive(self):
        num_traders_allowed = self.session.config['players_per_group']
        num_consented = 0

        for player in self.group.get_players():
            # Preset overbooked variable
            player.participant.vars['overbooked'] = False
            if player.participant.vars['consent'] == True:
                num_consented += 1
        
        # If more people consented to play then allowed then randomly select participants
        if (num_consented > num_traders_allowed):
            shuffled_players = self.group.get_players()
            random.shuffle(shuffled_players)

            for player in shuffled_players[num_traders_allowed:]:
                player.participant.vars['overbooked'] = True


    
class BlockDropouts(Page):
    def is_displayed(self):
        return self.round_number == 1 and self.player.consent == False

class Overbooked(Page):
    def is_displayed(self):
        return self.round_number == 1 and self.player.consent == True and self.player.participant.vars['overbooked'] == True

page_sequence = [Consent, ConsentWaitPage] #, BlockDropouts, Overbooked]
