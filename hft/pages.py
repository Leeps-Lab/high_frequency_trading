from ._builtin import Page, WaitPage
import logging
from django.core.cache import cache
from .cache import get_cache_key
from django.conf import settings
import json
import time
from .output import TraderRecord
from .session_results import elo_player_summary, state_for_results_template
from .utility import ensure_results_ready
from settings import test_inputs_dir
from .models import Constants, get_correct_answers, survey_round
import random

log = logging.getLogger(__name__)

# this module is under construction
# we will update this once we finish
# building the new environment components

class RegisterPlayers(WaitPage):
    def is_displayed(self):
        return self.round_number == 1

    def after_all_players_arrive(self):
        def my_custom_random(exclude, num_rounds):
            randInt = random.randint(1, num_rounds)
            return my_custom_random(exclude, num_rounds) if randInt in exclude else randInt 
        # Generate random round number
        num_rounds = self.session.config['num_rounds']
        exclude = self.session.config['trial_rounds']

        # Failsafe
        if num_rounds == len(exclude):
            self.session.config['random_round_num'] = random.randint(1, num_rounds)
        else:
            self.session.config['random_round_num'] = my_custom_random(exclude, num_rounds)
        self.subsession.register()


class Instructions(Page):
    def is_displayed(self):
        return self.round_number == 1 and self.player.participant.vars['consent'] == True and self.player.participant.vars['overbooked'] == False and self.player.participant.vars['underbooked'] == False
    
    def vars_for_template(self):
        out = {}

        out['auction_format'] = self.session.config['auction_format']
        out['next_button_timeout'] = self.session.config['instructions_next_button_timeout']
        return out


# beginning of survey page classes
class General(Page):
    form_model = 'player'
    # question fields and whether the participant chose the right answer at first
    lista=list(Constants.q_and_a_sections["general"].keys())
    form_fields = lista

    def vars_for_template(self):
        return get_correct_answers(Constants.q_and_a_sections, "general")

    def is_displayed(self):
        return self.round_number == Constants.num_rounds


class Inventory(Page):
    form_model = 'player'
    # question fields and whether the participant chose the right answer at first
    form_fields = list(Constants.q_and_a_sections["inventory"].keys()) + [question
                  + "_right_count" for question in 
                  Constants.q_and_a_sections["inventory"].keys()]

    def vars_for_template(self):
        return get_correct_answers(Constants.q_and_a_sections, "inventory")

    def is_displayed(self):
        practice_rounds = self.session.config['trial_rounds']
        return survey_round(self.round_number, practice_rounds)


class ExternalMarket(Page):
    form_model = 'player'
    # question fields and whether the participant chose the right answer at first
    form_fields = list(Constants.q_and_a_sections["external_market"].keys()) + [question
                  + "_right_count" for question in 
                  Constants.q_and_a_sections["external_market"].keys()]

    def vars_for_template(self):
        return get_correct_answers(Constants.q_and_a_sections, "external_market")

    def is_displayed(self):
        practice_rounds = self.session.config['trial_rounds']
        return survey_round(self.round_number, practice_rounds)


class Speed(Page):
    form_model = 'player'
    # question fields and whether the participant chose the right answer at first
    form_fields = list(Constants.q_and_a_sections["speed"].keys()) + [question
                  + "_right_count" for question in 
                  Constants.q_and_a_sections["speed"].keys()]

    def vars_for_template(self):
        return get_correct_answers(Constants.q_and_a_sections, "speed")

    def is_displayed(self):
        practice_rounds = self.session.config['trial_rounds']
        return survey_round(self.round_number, practice_rounds)


# final survey hft page class
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
        correct_answers_dicts = get_correct_answers(Constants.q_and_a_sections, "market_specific_design")
        auction_format = self.session.config['auction_format'].lower()
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

    def is_displayed(self):
        practice_rounds = self.session.config['trial_rounds']
        return survey_round(self.round_number, practice_rounds)


class InitialDecisionSelection(Page):
    form_model = 'player'
    form_fields = [
        'initial_slider_a_x',
        'initial_slider_a_y',
        'initial_slider_a_z',
        'initial_role',
        'initial_speed_on',
    ]

    def is_displayed(self):
        return self.round_number <= self.session.config['num_rounds'] and self.player.participant.vars['consent'] == True and self.player.participant.vars['overbooked'] == False and self.player.participant.vars['underbooked'] == False
    
    timeout_submission = {'initial_slider_a_x': 0,
        'initial_slider_a_y': 0,
        'initial_slider_a_z': 0,
        'initial_role': 'out',
        'initial_speed_on': False
    }
    
    # Auto advance page
    def get_timeout_seconds(self):
        timeout = self.session.config['auto_advance']
        print(timeout)
        if timeout > 0:
            return timeout
    
    def vars_for_template(self):
        is_trial_round = self.round_number in self.session.config['trial_rounds']
        return {
            'trial_round': is_trial_round
        }


class PreWaitPage(WaitPage):
    def is_displayed(self):
        return self.round_number <= self.session.config['num_rounds'] and self.player.participant.vars['consent'] == True and self.player.participant.vars['overbooked'] == False and self.player.participant.vars['underbooked'] == False

    def after_all_players_arrive(self):
        if self.round_number > 1:
            self.subsession.register()
            
        for player in self.group.get_players():
            if player.participant.vars['consent'] == True and player.participant.vars['overbooked'] == False and player.participant.vars['underbooked'] == False:
                cache_key = get_cache_key('from_kws',
                    model_id=player.id,
                    model_name='trader',
                    subsession_id=self.subsession.id
                )
                trader = cache.get(cache_key)
                trader.set_initial_strategy(
                    player.initial_slider_a_x,
                    player.initial_slider_a_y,
                    player.initial_slider_a_z,
                    player.initial_role,
                    player.initial_speed_on
                )
                cache.set(cache_key, trader)


class EloExperiment(Page):
    def is_displayed(self):
        return self.round_number <= self.session.config['num_rounds'] and self.player.participant.vars['consent'] == True and self.player.participant.vars['overbooked'] == False and self.player.participant.vars['underbooked'] == False

    def vars_for_template(self):
        if not self.session.config['test_input_file']:
            inputs_addr = None
        else:
            inputs_addr = test_inputs_dir.format(
                self.session.config['test_input_file'])

        initial_strategy = {
            'slider_a_x': self.player.initial_slider_a_x,
            'slider_a_y': self.player.initial_slider_a_y,
            'slider_a_z': self.player.initial_slider_a_z,
            'role': self.player.initial_role,
            'speed_on': self.player.initial_speed_on,
        }

        return {
            'inputs_addr': inputs_addr,
            'initial_strategy': initial_strategy,
        }

# class PostSessionWaitPage(WaitPage):
#     # I need an extra wait page
#     # since I am blocking at
#     # after all players arrive
#     # at actual wait page
#     template_name = 'hft/PostSessionWaitPage.html'

#     def socket_url(self):
#         return '/wait_page_results/{},{},{}/'.format(
#             self._session_pk,
#             self._index_in_pages,
#             self._channels_group_id_in_subsession()
#         )
#     def after_all_players_arrive(self):
#         print('arrived')

class PostSession(Page):
    def is_displayed(self):
        return self.round_number <= self.session.config['num_rounds'] and self.player.participant.vars['consent'] == True and self.player.participant.vars['overbooked'] == False and self.player.participant.vars['underbooked'] == False

    timeout_seconds = 25
    timer_text = 'Processing results..'

class ResultsWaitPage(WaitPage):
    def is_displayed(self):
        return self.round_number <= self.session.config['num_rounds'] and self.player.participant.vars['consent'] == True and self.player.participant.vars['overbooked'] == False and self.player.participant.vars['underbooked'] == False

    def after_all_players_arrive(self):
        # at some point we should add a
        # wait page to otree that checks
        # for results being ready without
        # blocking a worker.
        # this should do it for now.
        players_query = self.group.get_players()
        subsession_id = self.subsession.id
        market_id = self.group.id
        num_players = 0
        for player in players_query:
            if player.participant.vars['consent'] == True and player.participant.vars['overbooked'] == False and player.participant.vars['underbooked'] == False:
                num_players += 1
        if ensure_results_ready(
            subsession_id, market_id, TraderRecord, num_players):
            for p in players_query:
                if p.participant.vars['consent'] == True and p.participant.vars['overbooked'] == False and p.participant.vars['underbooked'] == False:
                    most_recent_state_record = TraderRecord.objects.get(
                        subsession_id=subsession_id, 
                        market_id=market_id, 
                        player_id=p.id,
                        trigger_event_type='market_end')
                    p.update_from_state_record(most_recent_state_record)
            try:
                for p in players_query:
                    if p.participant.vars['consent'] == True and p.participant.vars['overbooked'] == False and p.participant.vars['underbooked'] == False:
                        elo_player_summary(p)
            except Exception:
                log.exception('error transform results group {}'.format(market_id))
        else:
            log.error('timeout transform results group {}'.format(market_id))


class Results(Page):
    def is_displayed(self):
        return self.round_number <= self.session.config['num_rounds'] and self.player.participant.vars['consent'] == True and self.player.participant.vars['overbooked'] == False and self.player.participant.vars['underbooked'] == False

    # Auto advance results page
    def get_timeout_seconds(self):
        timeout = self.session.config['auto_advance']
        if timeout > 0:
            return timeout


    def vars_for_template(self):
        page_state = state_for_results_template(self.player, self.session.config['session_duration'], self.session.config['speed_unit_cost'] * .0001)
        # send as json so polymer likes it
        out = {k: json.dumps(v) for k, v in page_state.items()}
        out['next_button_timeout'] = self.session.config['next_button_timeout']
        
        if self.round_number == self.session.config['num_rounds']:
            self.send_payment_info_to_anonpay()

        return out
    
    def send_payment_info_to_anonpay(self):
        out = {'all_payoffs': []}
        num_rounds = self.session.config['num_rounds']
        out['num_rounds'] = num_rounds
        out['random_payoff'] = self.session.config['random_payoff']
        out['random_round_num'] = self.session.config['random_round_num']

        for i in range(num_rounds):
            if i in self.session.config['trial_rounds']:
                # Trial round isn't included in payoff
                out['all_payoffs'].append(0)
            else:
                out['all_payoffs'].append(round(self.player.in_round(i+1).net_worth * .0001, 2))
        
        out['random_round_payoff'] = out['all_payoffs'][out['random_round_num'] - 1]

        if out['random_payoff'] == False:
            out['sum_payoffs'] = sum(out['all_payoffs'])
        else:
            out['sum_payoffs'] = out['random_round_payoff']
        

        participation_fee = self.session.config['participation_fee']
        out['participation_fee'] = participation_fee
        
        exchange_rate = self.session.config['real_world_currency_per_point']
        out['exchange_rate'] = exchange_rate
        out['max_payoff'] = max(0, out['sum_payoffs'] * exchange_rate)
        out['total_cash_payment'] = participation_fee + out['max_payoff']

        # To send to AnonPay
        self.player.cummulative_payoff = out['total_cash_payment']

        if float(out['sum_payoffs']) < 0:
            # Negative payoff
            self.participant.vars['negative_payoff'] = True
            self.participant.vars['payment_before_participation_fee'] = 0
            self.participant.vars['payment'] = participation_fee
            self.participant.vars['earned_more_than_max'] = False
        else:
            # Positive payoff
            self.participant.vars['negative_payoff'] = False
            self.participant.vars['payment_before_participation_fee'] = out['total_cash_payment'] - participation_fee
            self.participant.vars['payment'] = out['total_cash_payment']

            if float(out['total_cash_payment']) > float(self.session.config['max_payment']):
                self.participant.vars['earned_more_than_max'] = True
                self.participant.vars['payment'] = float(self.session.config['max_payment']) + participation_fee
            else:
                self.participant.vars['earned_more_than_max'] = False

        self.participant.vars['random_payoff'] = out['random_payoff']
        self.participant.vars['random_round_num'] = out['random_round_num']
        self.participant.vars['participation_fee'] = participation_fee
        self.participant.vars['exchange_rate'] = out['exchange_rate']
        self.participant.vars['max_payment'] = self.session.config['max_payment']


# Last page in experiment to display all payoffs
class CumulativePayoff(Page):
    def is_displayed(self):
        return self.round_number == self.session.config['num_rounds'] + 1 and self.player.participant.vars['consent'] == True and self.player.participant.vars['overbooked'] == False and self.player.participant.vars['underbooked'] == False
    
    def vars_for_template(self):
        out = {'all_payoffs': []}
        num_rounds = self.session.config['num_rounds']
        out['num_rounds'] = num_rounds
        out['random_payoff'] = self.session.config['random_payoff']
        out['random_round_num'] = self.session.config['random_round_num']

        for i in range(num_rounds):
            if i in self.session.config['trial_rounds']:
                # Trial round isn't included in payoff
                out['all_payoffs'].append(0)
            else:
                out['all_payoffs'].append(round(self.player.in_round(i+1).net_worth * .0001, 2))
        
        out['random_round_payoff'] = out['all_payoffs'][out['random_round_num'] - 1]

        if out['random_payoff'] == False:
            out['sum_payoffs'] = sum(out['all_payoffs'])
        else:
            out['sum_payoffs'] = out['random_round_payoff']
        

        participation_fee = self.session.config['participation_fee']
        out['participation_fee'] = participation_fee
        
        exchange_rate = self.session.config['real_world_currency_per_point']
        out['exchange_rate'] = exchange_rate
        out['max_payoff'] = max(0, out['sum_payoffs'] * exchange_rate)
        out['total_cash_payment'] = participation_fee + out['max_payoff']

        # To send to AnonPay
        self.player.cummulative_payoff = out['total_cash_payment']

        if float(out['sum_payoffs']) < 0:
            # Negative payoff
            self.participant.vars['negative_payoff'] = True
            self.participant.vars['payment_before_participation_fee'] = 0
            self.participant.vars['payment'] = participation_fee
            self.participant.vars['earned_more_than_max'] = False
        else:
            # Positive payoff
            self.participant.vars['negative_payoff'] = False
            self.participant.vars['payment_before_participation_fee'] = out['total_cash_payment'] - participation_fee
            self.participant.vars['payment'] = out['total_cash_payment']

            if float(out['total_cash_payment']) > float(self.session.config['max_payment']):
                self.participant.vars['earned_more_than_max'] = True
                self.participant.vars['payment'] = float(self.session.config['max_payment']) + participation_fee
            else:
                self.participant.vars['earned_more_than_max'] = False

        self.participant.vars['random_payoff'] = out['random_payoff']
        self.participant.vars['random_round_num'] = out['random_round_num']
        self.participant.vars['participation_fee'] = participation_fee
        self.participant.vars['exchange_rate'] = out['exchange_rate']
        self.participant.vars['max_payment'] = self.session.config['max_payment']

        return out

page_sequence = [
    RegisterPlayers,
    Instructions,
    Inventory,
    ExternalMarket,
    Speed,
    MarketSpecific,
    InitialDecisionSelection,
    PreWaitPage,
    EloExperiment,
    # comment this to remove post-session 30 second wait
    # if data isn't ready in time w/ larger sessions, this may need to be uncommented
    # PostSession,
    ResultsWaitPage,
    Results,
    General,
    #CumulativePayoff,
]
