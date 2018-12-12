import os
import logging
import collect
import sys
import logging
import yaml

log = logging.getLogger(__name__)


class CustomOtreeConfig:
    yaml_configs_directory = os.path.join(os.getcwd(), 'session_config/session_configs')
    otree_default_required = {'app_sequence': ['hft_bcs']}

    def __init__(self, configs:dict, filename:str):
        self.base_configs = configs
        self.filename = filename
        self.environment = configs['environment']

    @classmethod
    def from_yaml(cls, filename) -> dict:
        path = os.path.join(cls.yaml_configs_directory, filename)
        with open(path, 'r') as f:
            try:
                configs = yaml.load(f)
            except yaml.YAMLError as e:
                raise e
            else:
                log.debug('read custom config: %s.' % path)
        return cls(configs, filename)

    def convert_to_otree_config(self, configs):
        otree_configs = {}
        yaml_to_otree_map = config_maps[self.environment]
        for otree_config_key, yaml_key in yaml_to_otree_map.items():
            parent_key, child_key = yaml_key
            otree_config_key = None
            try:
                otree_configs[otree_config_key] = configs[parent_key][child_key]
            except KeyError:
                raise KeyError('%s:%s is missing in %s, set to none.' % (
                    parent_key, child_key, self.filename))
        otree_configs.update(self.otree_default_required)
        return otree_configs

    @classmethod
    def initialize_many_from_folder(cls):
        """
        reads all files in config folder
        """
        all_yaml_filenames = os.listdir(cls.yaml_configs_directory)
        yaml_config_files = [f for f in all_yaml_filenames if f.endswith('.yaml')]
        custom_configs = [cls.from_yaml(f) for f in yaml_config_files]
        return custom_configs

config_maps = {
    'BCS': { 'name': ('session', 'session-name'),
        'display_name': ('market', 'design'),
        'num_demo_participants': ('demo', 'number-of-participants'),
        'environment': ('session', 'environment'),
        'trial': ('session', 'trial'),
        'trial_length': ('session', 'trial-length'),
        'num_rounds': ('session', 'num-rounds'),
        'restore': ('session', 'restore'),
        'restore_from': ('session', 'restore-from'),
        'design': ('market', 'design'),
        'exchange_host': ('market', 'matching-engine-host'),
        'num_markets': ('market', 'number-of-markets'),
        'number_of_groups': ('group', 'number-of-groups'),
        'players_per_group': ('group', 'players-per-group'),
        'speed_cost': ('parameters', 'speed-cost'),
        'fundamental_price': ('parameters', 'fundamental-price'),
        'initial_spread': ('parameters', 'initial-spread'),
        'max_spread': ('parameters', 'max-spread'),
        'initial_endowment': ('parameters', 'initial-endowment'),
        'session_length': ('parameters', 'session-length'),
        'group_matrix': ('group', 'group-assignments'),
        'batch_length': ('parameters', 'batch-length'),
        'random_round_payment': ('session', 'random-round-payment'),
        'participation_fee': ('session', 'participation-fee'),
        'real_world_currency_per_point': ('session', 'exchange-rate'),
        'exogenous_event_directory': ('session', 'exogenous_event_directory')
        }
}

