import os
import logging
import sys
import yaml

log = logging.getLogger(__name__)


class CustomOtreeConfig:
    otree_default_required = {'app_sequence': ['hft_bcs']}

    def __init__(self, configs:dict, filename:str):
        self.base_configs = configs
        self.filename = filename
        self.environment = configs['session']['environment']

    @classmethod
    def from_yaml(cls, path_to_file) -> dict:
        with open(path_to_file, 'r') as f:
            try:
                configs = yaml.load(f)
            except yaml.YAMLError as e:
                raise e
            else:
                log.debug('custom config: %s.' % path_to_file)
        return cls(configs, path_to_file)

    def get_otree_config(self) -> dict:
        otree_configs = {}
        yaml_to_otree_map = config_maps[self.environment]
        for otree_config_key, yaml_key in yaml_to_otree_map.items():
            parent_key, child_key = yaml_key
            try:
                otree_configs[otree_config_key] = self.base_configs[parent_key][child_key]
            except KeyError:
                log.info('%s:%s is missing in %s, set to none.' % (
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
        custom_configs = [cls.from_yaml(f) for f in yaml_config_filenames]
        return custom_configs

config_maps = {
    'BCS': { 'name': ('session', 'session-name'),
        'auction_format': ('market', 'auction-format'),
        'num_demo_participants': ('demo', 'number-of-participants'),
        'environment': ('session', 'environment'),
        'trial': ('session', 'trial'),
        'trial_length': ('session', 'trial-length'),
        'num_rounds': ('session', 'num-rounds'),
        'exchange_host': ('market', 'matching-engine-host'),
        'num_markets': ('market', 'number-of-markets'),
        'number_of_groups': ('group', 'number-of-groups'),
        'players_per_group': ('group', 'players-per-group'),
        'speed_cost': ('parameters', 'speed-cost'),
        'fundamental_price': ('parameters', 'fundamental-price'),
        'initial_spread': ('parameters', 'initial-spread'),
        'max_spread': ('parameters', 'max-spread'),
        'initial_endowment': ('parameters', 'initial-endowment'),
        'period_length': ('parameters', 'period-length'),
        'group_matrix': ('group', 'group-assignments'),
        'batch_length': ('parameters', 'batch-length'),
        'random_round_payment': ('session', 'random-round-payment'),
        'participation_fee': ('session', 'participation-fee'),
        'real_world_currency_per_point': ('session', 'exchange-rate'),
        'exogenous_event_directory': ('session', 'exogenous-event-directory'),
        'investor_arrivals': ('exogenous-events', 'investor-arrivals'),
        'fundamental_value_jumps': ('exogenous-events', 'fundamental-value-jumps'),
        },
        'LEEPS': { 
            'name': ('session', 'session-name'),
            'auction_format': ('market', 'auction-format'),
            'num_demo_participants': ('demo', 'number-of-participants'),
            'environment': ('session', 'environment'),
            'trial': ('session', 'trial'),
            'trial_length': ('session', 'trial-length'),
            'num_rounds': ('session', 'num-rounds'),
            'exchange_host': ('market', 'matching-engine-host'),
            'num_markets': ('market', 'number-of-markets'),
            'number_of_groups': ('group', 'number-of-groups'),
            'players_per_group': ('group', 'players-per-group'),
            'speed_cost': ('parameters', 'speed-cost'),
            'fundamental_price': ('parameters', 'fundamental-price'),
            'initial_spread': ('parameters', 'initial-spread'),
            'max_spread': ('parameters', 'max-spread'),
            'initial_endowment': ('parameters', 'initial-endowment'),
            'period_length': ('parameters', 'period-length'),
            'group_matrix': ('group', 'group-assignments'),
            'batch_length': ('parameters', 'batch-length'),
            'random_round_payment': ('session', 'random-round-payment'),
            'participation_fee': ('session', 'participation-fee'),
            'real_world_currency_per_point': ('session', 'exchange-rate'),
            'exogenous_event_directory': ('session', 'exogenous-event-directory'),
            'investor_arrivals': ('exogenous-events', 'investor-arrivals'),
            'grid_size': ('parameters', 'grid-size')
        }
}

