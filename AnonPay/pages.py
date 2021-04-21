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
    def vars_for_template(self):
        vft = {'nicePayment': formatNicely(self.participant.vars['payment']), 'emailEntered': self.player.email}
        
        self.player.email = '[REDACTED]'
        
        return vft


class Details(PageWithAmount):
    form_fields = ['email']
    form_model = 'player'
    
    timeout_seconds = 5*60
    
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
                
                lines.append(f'"{self.player.email}";"{self.participant.vars["payment"]}"')
                
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


class EndFeedback(PageWithAmount):
    form_model = 'player'
    form_fields = ['feedback']


page_sequence = [Details, EndFeedback]
