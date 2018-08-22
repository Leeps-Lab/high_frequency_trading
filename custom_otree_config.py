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
        self.fields = {}
        for pair in cls.yaml_map:
            config_key = pair[0]
            key_head = pair[1][0]
            key_sub = pair[1][1]
            try:
                config_value = self.yaml_conf[key_head][key_sub]
            except KeyError:
                log.msg('%s:%s is missing, set to None.' % (key_head, key_sub))
                config_value = None
            field = {config_key: config_value}
            self.fields.update(field)
        self.fields.update(cls.constant_required)
        self.read_csv()
        self.format_display_name()
        self.format_session_name()
        if hasattr(self, 'read_group_matrix'):
            self.read_group_matrix()

    def read(self, filename):
        cls = self.__class__
        path = os.path.join(cls.sess_conf_dir, filename)
        with open(path, 'r') as f:
            try:
                config = yaml.load(f)
            except yaml.YAMLError as e:
                config = False
                raise e
            else:
                log.msg('reading custom config: %s.' % path)
        return config

    
    @classmethod
    def get_all(cls):
        dirc = cls.sess_conf_dir
        all_files = os.listdir(dirc)
        config_files = [f for f in all_files if f.endswith('.yaml')]
        custom_configs = [cls(f) for f in config_files]
        return custom_configs
    
    def get_fields(self):
        return self.fields
    
    def read_csv(self):
        cls = self.__class__
        dir_field = cls.yaml_map[-1][0] # last field in map
        folder = self.fields.get(dir_field, None)
        if folder is None:
            raise ValueError('session folder name is missing.')
        dirc = os.path.join(cls.conf_dir, folder)
        fields = {}
        for field in cls.exogenous_input:
            for k, v in self.yaml_conf[field].items():
                label = '{field}_{key}'.format(field=field, key=k)
                csv_name = collect.extract_name(v)
                csv_path = os.path.join(dirc, csv_name)
                fields.update({label: csv_path})
        self.fields.update(fields)

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
        ('name', ('market', 'design')),
        ('display_name', ('market', 'design')),
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
        f = self.fields
        name = """High Frequency Trading - BCS - {}
            length: {}, groups: {}, players per group: {}, speed cost: {},
            folder: {} """.format( f['design'], f['session_length'], 
            f['number_of_groups'], f['players_per_group'], f['speed_cost'], 
            f['folder'])
        self.fields['display_name'] = name
    
    def format_session_name(self):
        f = self.fields
        name = 'HFT_{}_{}'.format(f['design'], f['folder'])
        name = name.replace('/', '_')
        self.fields['name'] = name

    def read_group_matrix(self):
        f = self.fields
        string_matrix = f['group_matrix']
        group_matrix = eval(string_matrix)
        f['group_matrix'] = group_matrix
        self.fields = f
        
