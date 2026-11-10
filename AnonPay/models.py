from otree.api import (
    models,
    widgets,
    BaseConstants,
    BaseSubsession,
    BaseGroup,
    BasePlayer,
    Currency as c,
    currency_range,
)


author = 'AnonPay'

doc = """
AnonPay (CPY/TDY oTree equivalent, the other algorithms are in anonpay.py)
"""


class Constants(BaseConstants):
    name_in_url = 'AnonPay'
    players_per_group = None
    num_rounds = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    error = models.StringField(initial = '')
    email = models.StringField(initial = '')
    emergency_code = models.StringField(initial = '')
    
    feedback = models.LongStringField(blank = True)
