from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants, get_correct_answers
from . import utility


class General(Page):
    form_model = 'player'
    # question fields and whether the participant chose the right answer at first
    form_fields = list(Constants.q_and_a_sections["general"].keys()) + [question
                  + "_right_first" for question in 
                  Constants.q_and_a_sections["general"].keys()]

    def vars_for_template(self):
        return get_correct_answers(Constants.q_and_a_sections, "general")


class Inventory(Page):
    form_model = 'player'
    # question fields and whether the participant chose the right answer at first
    form_fields = list(Constants.q_and_a_sections["inventory"].keys()) + [question
                  + "_right_first" for question in 
                  Constants.q_and_a_sections["inventory"].keys()]

    def vars_for_template(self):
        return get_correct_answers(Constants.q_and_a_sections, "inventory")


class ExternalMarket(Page):
    form_model = 'player'
    # question fields and whether the participant chose the right answer at first
    form_fields = list(Constants.q_and_a_sections["external_market"].keys()) + [question
                  + "_right_first" for question in 
                  Constants.q_and_a_sections["external_market"].keys()]

    def vars_for_template(self):
        return get_correct_answers(Constants.q_and_a_sections, "external_market")


class Speed(Page):
    form_model = 'player'
    # question fields and whether the participant chose the right answer at first
    form_fields = list(Constants.q_and_a_sections["speed"].keys()) + [question
                  + "_right_first" for question in 
                  Constants.q_and_a_sections["speed"].keys()]

    def vars_for_template(self):
        return get_correct_answers(Constants.q_and_a_sections, "speed")


class MarketSpecific(Page):
    form_model = 'player'
    # question fields and whether the participant chose the right answer at first
    form_fields = list(Constants.q_and_a_sections["market_specific_design"].keys()) + [question
                  + "_right_first" for question in 
                  Constants.q_and_a_sections["market_specific_design"].keys()]

    def vars_for_template(self):
        correct_answers_dicts = get_correct_answers(Constants.q_and_a_sections, "market_specific_design")
        correct_answers = {} # placeholder for storing correct answers
        for question in correct_answers_dicts.keys():
            # setting correct answer per question
            auction_format = self.session.config['auction_format'].lower()
            correct_answers[question] = correct_answers_dicts[auction_format]
        
        return correct_answers


page_sequence = [
    General,
    Inventory,
    ExternalMarket,
    Speed,
    MarketSpecific
]
