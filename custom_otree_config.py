import os
import logging
import yaml
import collect
import sys
from twisted.python import log

log.startLogging(sys.stdout)

class CustomOtreeConfig:
    yaml_map = ()
    token = ''
    conf_dir = ''
    sess_conf_dir = ''
    required = ()
    exogenous_input = ()
    constant_required = {}

    def __init__(self, filename):
        self.yaml_conf = self.read(filename)
        cls = self.__class__
        for pair in cls.yaml_map:
            config_key = pair[0]
            key_head = pair[1][0]
            key_sub = pair[1][1]
            try:
                config_value = self.yaml_conf[key_head][key_sub]
            except KeyError:
                log.msg('%s:%s is missing, set to None.' % (key_head, key_sub))
                config_value = None
            setattr(self, config_key, config_value)
        self.read_csv()
        self.format_display_name()
        if hasattr(self, 'read_group_matrix'):
            self.read_group_matrix()


    def read(self, filename):
        cls = self.__class__
        path = os.path.join(cls.sess_conf_dir, filename)
        with open(path, 'r') as f:
            try:
                config = yaml.load(f)
            except yaml.YAMLError as e:
                raise e
            else:
                log.msg('reading custom config: %s.' % path)
        return config

    
    @classmethod
    def get_all(cls):
        """
        reads all files in config folder
        """
        dirc = cls.sess_conf_dir
        all_files = os.listdir(dirc)
        config_files = [f for f in all_files if f.endswith('.yaml')]
        custom_configs = [cls(f) for f in config_files]
        return custom_configs

    def read_csv(self):
        cls = self.__class__
        dir_field = cls.yaml_map[-1][0] # last field in map
        folder = getattr(self, dir_field)
        if folder is None:
            raise ValueError('session folder name is missing.')
        dirc = os.path.join(cls.conf_dir, folder)
        self.csv_labels = {}
        for field in cls.exogenous_input:
            for k, v in self.yaml_conf[field].items():
                for r, f in enumerate(v):
                    label = '{field}_{key}_round_{round}'.format(field=field, key=k, round=r+1)
                    csv_name= os.path.join(dirc, f)
                    self.csv_labels[label] = csv_name
                    
               # csv_list = os.path.join(dirc, v)
    
    def json_format(self):
        cls = self.__class__
        out = {k[0]: getattr(self, k[0]) for k in cls.yaml_map}
        out.update(self.csv_labels)
        constant = {k: v for k, v in cls.constant_required.items()}
        out.update(constant)
        return out

    def format_display_name(self):
        pass
    
    def format_session_name(self):
        raise NotImplementedError()

class BCSConfig(CustomOtreeConfig):

    constant_required = {'app_sequence': ['hft_bcs']}
    conf_dir = os.path.join(os.getcwd(), 'session_config')
    sess_conf_dir = os.path.join(conf_dir, 'session_configs')
    token = 'fd97e675ca58325e88ea7339ec641bb4a1193548'
    yaml_map = (
        ('name', ('session', 'session_name')),
        ('display_name', ('market', 'design')),
        ('trial', ('trial', 'run')),
        ('trial_length', ('trial', 'trial-length')),
        ('num_rounds', ('session', 'num-rounds')),
        ('restore', ('session', 'restore')),
        ('restore_from', ('session', 'restore-from')),
        ('design', ('market', 'design')),
        ('exchange_host', ('market', 'matching-engine-host')),
        ('number_of_groups', ('group', 'number-of-groups')),
        ('players_per_group', ('group', 'players-per-group')),
        ('speed_cost', ('parameters', 'speed-cost')),
        ('num_demo_participants', ('demo', 'number-of-participants')),
        ('fundamental_price', ('parameters', 'fundamental-price')),
        ('initial_spread', ('parameters', 'initial-spread')),
        ('max_spread', ('parameters', 'max-spread')),
        ('initial_endowment', ('parameters', 'initial-endowment')),
        ('session_length', ('parameters', 'session-length')),
        ('group_matrix', ('group', 'group-assignments')),
        ('batch_length', ('parameters', 'batch-length')),
        # field below is mandatory
        # has to be last field in the map.
        # it is used in reading csvs.
        ('folder', ('directory', 'folder'))
    )
    exogenous_input = ('investors', 'jumps')

    def format_display_name(self):
        name = """High Frequency Trading - BCS - {self.design} \n
            length: {self.session_length}, groups: {self.number_of_groups}, 
            players per group: {self.players_per_group}, speed cost: {self.speed_cost},
            folder: {self.folder} """.format(self=self)
        setattr(self, 'display_name', name)

    def read_group_matrix(self):
        string_matrix = getattr(self, 'group_matrix')
        group_matrix = eval(string_matrix)
        setattr(self, 'group_matrix', group_matrix)
        
