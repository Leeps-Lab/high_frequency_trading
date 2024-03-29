from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants

import random, os

try:
    import fcntl
except ModuleNotFoundError:
    pass


def formatNicely(amount):
    return "{:.2f}".format(amount)
    # return "{:.2f}".format(amount).replace('.', ',') # for EUR


class PageWithAmount(Page):
    #timeout_seconds = 5*60
    def vars_for_template(self):
        try:
            vft = {
                    'random_payoff': self.participant.vars['random_payoff'],
                    'random_round_num': self.participant.vars['random_round_num'],
                    'earned_more_than_max': self.participant.vars['earned_more_than_max'],
                    'participation_fee': self.participant.vars['participation_fee'],
                    'exchange_rate': self.participant.vars['exchange_rate'],
                    'total_cash_payment_before_exchange_rate': float(self.participant.vars['payment_before_participation_fee'] / self.participant.vars['exchange_rate']),
                    'negative_payoff': self.participant.vars['negative_payoff'],
                    'max_payment': self.player.participant.vars['max_payment'],
                    }
        except:
            vft = {
                    'random_payoff': False,
                    'random_round_num': 0,
                    'earned_more_than_max': False,
                    'participation_fee': self.participant.vars['payment'],
                    'exchange_rate': 0,
                    'negative_payoff': False,
                    }
        
        vft['emailEntered'] = self.player.email
        vft['feedback_next_button_timeout'] = self.session.config['feedback_next_button_timeout']
        vft['consent'] = self.player.participant.vars['consent']
        vft['overbooked'] = self.player.participant.vars['overbooked']
        vft['underbooked'] = self.player.participant.vars['underbooked']
        vft['nicePayment'] = formatNicely(self.participant.vars['payment'])


        self.player.email = '[REDACTED]'
        return vft

class Feedback(PageWithAmount):
    def is_displayed(self):
        return self.player.participant.vars['consent'] == True and self.player.participant.vars['overbooked'] == False and self.player.participant.vars['underbooked'] == False



class Details(PageWithAmount):
    form_fields = ['email']
    form_model = 'player'
    
    #timeout_seconds = 5*60
    
    def before_next_page(self):
        self.player.emergency_code = ''.join(random.choices(list('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'), k = 8))
        
        try:
            pfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), "payments", self.session.code + ".csv")
            
            with open(pfile, "a+") as fp:
                try:
                    fcntl.flock(fp, fcntl.LOCK_EX)
                except NameError:
                    pass
                
                fp.seek(0)
                
                lines = fp.read().splitlines()

                player_status = ''

                if self.participant.vars["consent"]:
                    if self.participant.vars["overbooked"]:
                        player_status = 'Overbooked'
                    elif self.participant.vars["underbooked"]:
                        player_status = 'Underbooked'
                    else:
                        player_status = 'Consented'
                else:
                    player_status = 'Did not consent'
                
                lines.append(f'Email: {self.player.email}, Payment Amount: {self.participant.vars["payment"]}, {player_status}')
                
                random.shuffle(lines)
                
                fp.seek(0)
                fp.truncate()
                
                fp.write('\n'.join(lines))
                
                try:
                    fcntl.flock(fp, fcntl.LOCK_UN)
                except NameError:
                    pass
        except:
            # This should not happen, but if the payment file is not writable, we will write all data
            # to the first subject's error variable.

            self.group.get_players()[0].error = self.group.get_players()[0].error + "email: " + self.player.email + ", payment: " + str(self.participant.vars["payment"]) + " | "


class FinalPage(PageWithAmount):
    #timeout_seconds = 5*60
    form_model = 'player'
    form_fields = ['feedback']


page_sequence = [Feedback, Details, FinalPage]
