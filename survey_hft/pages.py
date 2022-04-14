from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants


# TODO: Chequear que los pagos mostrados al final sean la suma de los pagos en cada juego

class Survey(Page):
    form_model = 'player'
    form_fields = ['problems', 'problems_text', 'strategy',
                   'satisfaction_with_strat', 'understanding',
                   'understanding_text', 'age', 'gender',
                   'suggestions', 'eval_underst', 'ubicacion']

    def is_displayed(self):
        # if self.participant.vars['MobilePhones'] is False and self.participant.vars['timed_out'] is False:
        if self.participant.vars['MobilePhones'] is False:
            return True
        else:
            return False

    def vars_for_template(self):
        return {'participant_id': self.participant.label, 'language': language}


class LastPage(Page):
    def vars_for_template(self):
        return {'participant_id': self.participant.label, 'language': language}


page_sequence = [
    Survey,
    LastPage
]
