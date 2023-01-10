from otree.api import Currency as c, currency_range
from . import pages
from ._builtin import Bot
from .models import Constants


class PlayerBot(Bot):
    def play_round(self):
        yield pages.Details, {'email': str(self.player.id)}
        yield pages.EndFeedback
