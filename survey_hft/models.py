from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)


author = 'Marco Gutierrez'

doc = """
General Final Quiz - MTurk
"""


class Constants(BaseConstants):
    name_in_url = 'quiz'
    players_per_group = None
    num_rounds = 1

    english_labels = dict(age='What is your age?', gender='What is your gender?',
                          strategy='Please describe the strategy that you used in making your decisions:',
                          problems='Did you encounter any problems while completing the task?',
                          problems_text='If so, please describe the problems you encountered:',
                          satisfaction_with_strat='You were satisfied with your strategy:',
                          understanding='You understood the whole study:',
                          understanding_text='If not, please explain:',
                          )
    spanish_labels = dict(age='¿Cuál es tu edad?', gender='¿Cuál es tu género?',
                          strategy='Por favor, describa la estrategia que usaste para tomar decisiones:',
                          problems='¿Encontraste algún problema cuando completaste la tarea?',
                          problems_text='De ser así, por favor describe los problemas encontrados:',
                          satisfaction_with_strat='¿Estuviste satisfecho con tu estrategia?',
                          understanding='¿Entendiste el estudio?',
                          understanding_text='Si no, describa por qué:',
                          )
    english_answers = dict(gender=[['Male', 'Male'], ['Female', 'Female']],
                           problems=[['Yes', 'Yes'], ['No', 'No']],
                           satisfaction_with_strat=[['Strongly Agree', 'Strongly Agree'], ['Agree', 'Agree'],
                                                    ['Neutral', 'Neutral'], ['Disagree', 'Disagree'],
                                                    ['Strongly Disagree', 'Strongly Disagree']],
                           understanding=[['Strongly Agree', 'Strongly Agree'], ['Agree', 'Agree'],
                                          ['Neutral', 'Neutral'], ['Disagree', 'Disagree'],
                                          ['Strongly Disagree', 'Strongly Disagree']],
                           )
    spanish_answers = dict(gender=[['Hombre', 'Hombre'], ['Mujer', 'Mujer'], ['Otro', 'Otro']],
                           problems=[['Sí', 'Sí'],['No', 'No']],
                           satisfaction_with_strat=[['Muy de Acuerdo', 'Muy de Acuerdo'], ['De Acuerdo', 'De Acuerdo'],
                                                    ['Neutral', 'Neutral'], ['En Desacuerdo', 'En Desacuerdo'],
                                                    ['Muy en Desacuerdo', 'Muy en Desacuerdo']],
                           understanding=[['Muy de Acuerdo', 'Muy de Acuerdo'], ['De Acuerdo', 'De Acuerdo'],
                                                    ['Neutral', 'Neutral'], ['En Desacuerdo', 'En Desacuerdo'],
                                                    ['Muy en Desacuerdo', 'Muy en Desacuerdo']],
                           )


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):

    age = models.IntegerField(label=Constants.spanish_labels['age'], min=18, max=125)

    gender = models.StringField(
        choices= Constants.spanish_answers['gender'],
        label= Constants.spanish_labels['gender'],
        widget=widgets.RadioSelect,
    )

    survey_timeout = models.IntegerField(initial=0)

    total_earnings_dollar = models.CharField()
    
    strategy = models.LongStringField(label=Constants.spanish_labels['strategy'])

    problems = models.CharField(label=Constants.spanish_labels['problems']
    ,choices=Constants.spanish_answers['problems'], widget=widgets.RadioSelect)

    problems_text = models.LongStringField(label=Constants.spanish_labels['problems_text'],
    blank=True)

    satisfaction_with_strat = models.CharField(label=Constants.spanish_labels['satisfaction_with_strat']
                                               ,choices=Constants.spanish_answers['satisfaction_with_strat']
                                               ,widget=widgets.RadioSelect)
