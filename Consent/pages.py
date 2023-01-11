from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants
import math
import time
import random


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
        num_traders_allowed = self.session.config['number_of_traders']
        consented_players = []

        for player in self.group.get_players():
            # Preset booked variable
            player.participant.vars['overbooked'] = False
            player.participant.vars['underbooked'] = False

            if player.participant.vars['consent'] == True:
                consented_players.append(player)
        
        num_consented = len(consented_players)
        
        # If more people consented to play then allowed then randomly select participants
        if (num_consented > num_traders_allowed):
            random.shuffle(consented_players)

            # Set players that were overbooked
            for player in consented_players[num_traders_allowed:]:
                player.participant.vars['overbooked'] = True
        
        # If less people consented then the number defined, cancel experiment
        if (num_consented < num_traders_allowed and self.session.config['allow_underbooking'] == False):
            for player in consented_players:
                player.participant.vars['underbooked'] = True

class BlockDropouts(Page):
    def is_displayed(self):
        return self.round_number == 1 and self.player.consent == False

class Overbooked(Page):
    def is_displayed(self):
        return self.round_number == 1 and self.player.consent == True and self.player.participant.vars['overbooked'] == True

page_sequence = [Consent, ConsentWaitPage] #, BlockDropouts, Overbooked]
