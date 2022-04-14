from otree.api import Currency as c, currency_range
from . import pages
from ._builtin import Bot
from .models import Constants


class PlayerBot(Bot):

    def play_round(self):
        yield (pages.SurveyInformation)
        yield (pages.Survey, {'strategy': 'Bot random strategy',
                              'problems': 'No',
                              'problems_text': 'Player is a Bot',
                              'satisfaction_with_strat': 'Strongly Agree',
                              'understanding': 'Strongly Agree',
                              'understanding_text': 'Bot'})
        yield (pages.FinalTaskResults)
