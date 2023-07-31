import os
import logging
import sys
import yaml
import random

class CustomOtreeConfig:
    otree_default_required = {'app_sequence': ['Consent', 'hft', 'AnonPay']}

    def __init__(self, configs:dict, filename:str):
        self.base_configs = configs
        self.filename = filename
        self.environment = configs['session']['environment']

    @classmethod
    def from_yaml(cls, path_to_file) -> dict:
        with open(path_to_file, 'r') as f:
            try:
                configs = yaml.load(f,Loader=yaml.FullLoader)
            except yaml.YAMLError as e:
                raise e
        return cls(configs, path_to_file)

    def get_otree_config(self) -> dict:
        otree_configs = {}
        yaml_to_otree_map = config_maps[self.environment]
        for otree_config_key, yaml_key in yaml_to_otree_map.items():
            parent_key, child_key = yaml_key
            try:
                value = self.base_configs[parent_key][child_key]
                otree_configs[otree_config_key] = value

            except KeyError:
                otree_configs[otree_config_key] = None
                sys.stdout.write('%s:%s is missing in %s, set to none.\n' % (
                    parent_key, child_key, self.filename))
        otree_configs.update(self.otree_default_required)
        
        return otree_configs

    @classmethod
    def initialize_many_from_folder(cls, directory):
        """
        reads all files in config folder
        """
        all_yaml_filenames = os.listdir(directory)
        yaml_config_filenames = [os.path.join(directory, f) for f in all_yaml_filenames 
            if f.endswith('.yaml')]
        custom_configs = []
        for f in yaml_config_filenames:
            try:
               config  = cls.from_yaml(f)
            except Exception as e:
                sys.stdout.write('failed to read file %s:%s\n', f, e)
            else:
                custom_configs.append(config)
        return custom_configs

config_maps = {
    'BCS': { 
        'name': ('session', 'session-name'),
        'auction_format': ('market', 'auction-format'),
        'num_demo_participants': ('demo', 'number-of-participants'),
        'environment': ('session', 'environment'),
        'trial': ('session', 'trial'),
        'trial_length': ('session', 'trial-length'),
        'num_rounds': ('session', 'num-rounds'),
        'exchange_host': ('market', 'matching-engine-host'),
        'num_markets': ('market', 'number-of-markets'),
        'number_of_traders': ('traders', 'number-of-traders'),
        'allow_underbooking': ('traders', 'allow-underbooking'),
        'technology_unit_cost': ('parameters', 'technology-unit-cost'),
        'fundamental_price': ('parameters', 'fundamental-price'),
        'initial_spread': ('parameters', 'initial-spread'),
        'max_spread': ('parameters', 'max-spread'),
        'initial_endowment': ('parameters', 'initial-endowment'),
        'period_length': ('parameters', 'period-length'),
        'batch_length': ('parameters', 'batch-length'),
        'random_round_payment': ('session', 'random-round-payment'),
        'participation_fee': ('session', 'participation-fee'),
        'real_world_currency_per_point': ('session', 'exchange-rate'),
        'exogenous_event_directory': ('session', 'exogenous-event-directory'),
        'investor_arrivals': ('exogenous-events', 'investor-arrivals'),
        'fundamental_value_jumps': ('exogenous-events', 'fundamental-value-jumps'),
        'auto_advance': ('session', 'auto-advance'),
        'next_button_timeout': ('session', 'next-button-timeout'),
        'random_payoff': ('session', 'random-payoff'),
        'max_payment': ('session', 'max-payment'),
        'instructions_next_button_timeout': ('session', 'instructions-next-button-timeout'),
        'feedback_next_button_timeout': ('session', 'feedback-next-button-timeout'),
        'trial_rounds': ('session', 'trial-rounds'),
        'run_survey': ('session', 'run-survey'),
    },
    'elo': { 
        'name': ('session', 'session-name'),
        'display_name': ('session', 'display-name'),
        'real_world_currency_per_point': ('session', 'exchange-rate'),
        'auction_format': ('market', 'auction-format'),
        'participation_fee': ('session', 'participation-fee'),
        'num_demo_participants': ('demo', 'number-of-participants'),
        'environment': ('session', 'environment'),
        'num_rounds': ('session', 'num-rounds'),
        'matching_engine_host': ('market', 'matching-engine-host'),
        'number_of_traders': ('traders', 'number-of-traders'),
        'allow_underbooking': ('traders', 'allow-underbooking'),
        'k_reference_price': ('parameters', 'k-reference-price'),
        'k_signed_volume': ('parameters', 'k-signed-volume'),
        'tax_rate': ('parameters', 'deduction-rate'),
        'include_signed_volume_widgets': ('parameters', 'include-signed-volume-widgets'),
        'include_manual_role': ('parameters', 'include-manual-role'),
        'speed_unit_cost': ('parameters', 'technology-unit-cost'),
        'initial_endowment': ('parameters', 'initial-endowment'),
        'session_duration': ('parameters', 'session-duration'),
        'batch_length': ('parameters', 'batch-length'),
        'investor_arrivals': ('exogenous-events', 'investor-arrivals'),
        'external_feed': ('exogenous-events', 'external-feed'),
        'default_role': ('parameters', 'default-role'),
        'test_input_file': ('tests', 'test_input_file'),
        'peg_proportion': ('parameters', 'peg-proportion'),
        'post_session_delay': ('session', 'post-session-delay'),
        'auto_advance': ('session', 'auto-advance'),
        'next_button_timeout': ('session', 'next-button-timeout'),
        'random_payoff': ('session', 'random-payoff'),
        'max_payment': ('session', 'max-payment'),
        'instructions_next_button_timeout': ('session', 'instructions-next-button-timeout'),
        'feedback_next_button_timeout': ('session', 'feedback-next-button-timeout'),
        'trial_rounds': ('session', 'trial-rounds'),
        'run_survey': ('session', 'run-survey'),
    }
}

