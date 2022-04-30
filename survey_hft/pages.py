from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants, get_correct_answers



class General(Page):
    form_model = 'player'
    # question fields and whether the participant chose the right answer at first
    lista=list(Constants.q_and_a_sections["general"].keys())
    form_fields = lista


    def vars_for_template(self):
        return get_correct_answers(Constants.q_and_a_sections, "general")


class Inventory(Page):
    form_model = 'player'
    # question fields and whether the participant chose the right answer at first
    form_fields = list(Constants.q_and_a_sections["inventory"].keys()) + [question
                  + "_right_count" for question in 
                  Constants.q_and_a_sections["inventory"].keys()] 
    def vars_for_template(self):
        return get_correct_answers(Constants.q_and_a_sections, "inventory")


class ExternalMarket(Page):
    form_model = 'player'
    # question fields and whether the participant chose the right answer at first
    form_fields = list(Constants.q_and_a_sections["external_market"].keys()) + [question
                  + "_right_count" for question in 
                  Constants.q_and_a_sections["external_market"].keys()]

    def vars_for_template(self):
        return get_correct_answers(Constants.q_and_a_sections, "external_market")


class Speed(Page):
    form_model = 'player'
    # question fields and whether the participant chose the right answer at first
    form_fields = list(Constants.q_and_a_sections["speed"].keys()) + [question
                  + "_right_count" for question in 
                  Constants.q_and_a_sections["speed"].keys()] 

    def vars_for_template(self):
        return get_correct_answers(Constants.q_and_a_sections, "speed")


class MarketSpecific(Page):
    form_model = 'player'
    # question fields and whether the participant chose the right answer at first
    def get_form_fields(self):
        auction_format = self.session.config['auction_format'].lower()

        if auction_format == "iex":
            return ["one_ask", "hidden_order", "one_ask_right_count", "hidden_order_right_count"]
        else:
            return ["one_ask", "one_ask_right_count"]

    def vars_for_template(self):
        auction_format = self.session.config['auction_format'].lower()
        correct_answers_dicts = get_correct_answers(Constants.q_and_a_sections, "market_specific_design")
        correct_answers = {} # placeholder for storing correct answers

        for question in correct_answers_dicts.keys():
            # setting correct answer per question
            if question == 'one_ask':
                auction_format = self.session.config['auction_format'].lower()
                correct_answers[question] = correct_answers_dicts[question][auction_format]
            else:
                correct_answers[question] = correct_answers_dicts[question]
        
        output = {**correct_answers, **{"auction": auction_format}} # adding auction format to output
        return output

page_sequence = [
    General,
    Inventory,
    ExternalMarket,
    Speed,
    MarketSpecific
]
