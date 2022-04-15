from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)

import json


author = 'Marco Gutierrez'

doc = """
General Understanding Quiz
"""


class Constants(BaseConstants):
    name_in_url = 'quiz'
    players_per_group = None
    num_rounds = 1

    # reading questions and answers
    q_and_a_path = "survey_hft/q_and_a.json"
    with open(q_and_a_path) as json_file:
        q_and_a = json.load(json_file)
        q_and_a_sections = q_and_a["sections"]


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

    # general questions
    for subject, q_and_a_subject in Constants.q_and_a_sections["general"].items():
        # creating field question
        if "command" not in q_and_a_subject["answers"][0]: # if choices are not created by command
            locals()[subject] = models.StringField( # generating field from dict
                label = q_and_a_subject["question"],
                choices = q_and_a_subject["answers"]
            )
        else:
            command = q_and_a_subject["answers"][0].replace("command: ", "")
            
            locals()[subject] = models.StringField( # generating field from dict
                label = q_and_a_subject["question"],
                choices = q_and_a_subject["answers"]
            )

        locals()[subject + "_right_first"] = models.BooleanField() # creating "player chose right answer from the beginning" field

    del subject
    del q_and_a_subject

    # rest of sections
    remaining_sections = list(Constants.q_and_a_sections.keys()).remove("general")
    for section in remaining_sections:
        for subject, q_and_a_subject in Constants.q_and_a_sections[f"{section}"].items():        
            locals()[subject] = models.StringField( # generating field from dict
                label = q_and_a_subject["question"],
                choices = q_and_a_subject["answers"]
            )

            locals()[subject + "_right_first"] = models.BooleanField() # creating "player chose right answer from the beginning" field
        
    del subject
    del q_and_a_subject