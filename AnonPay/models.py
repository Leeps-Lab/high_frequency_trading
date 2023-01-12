from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)

import random

author = 'MRPG'

doc = """
CLERPAY end HFT
"""


class Constants(BaseConstants):
    name_in_url = 'clerpay_end_hft'
    players_per_group = None
    num_rounds = 1


class Subsession(BaseSubsession):
    def creating_session(self):
        for p in self.get_players():
            p.transaction_code = random.randrange(100000000, 999999999)


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    transaction_code = models.IntegerField()
