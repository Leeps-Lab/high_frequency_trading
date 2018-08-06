import yaml
import os
import collect

configs_are_in = 'session_config/session_configs'
all_configs_dir = os.path.join(os.getcwd(), configs_are_in)

my_token = 'fd97e675ca58325e88ea7339ec641bb4a1193548'


def find_all(directory, string_end):
    all_files = os.listdir(directory)
    config_files = [f for f in all_files if f.endswith(string_end)]
    return config_files


def read(filename):
    path = os.path.join(all_configs_dir, filename)
    with open(path, 'r') as f:
        try:
            config = yaml.load(f)
        except yaml.YAMLError as e:
            config = False
            raise (e)
        else:
            print('Found a custom config: %s.' % filename)
    return config


def create(config, filename):   
    # TODO: Consider refactoring this 
    custom_config = dict()
    try:
        clean_name = filename.split('.')[0]
        custom_config = {
            'name': 'HFT' + '_' + config['market']['design'] + '_' + clean_name,
            'display_name': 'High Frequency Trading ' + config['market']['design'] + ' ' + clean_name,
            'exchange_host': config['market']['matching-engine-host'],
            'number_of_groups': config['group']['number-of-groups'],
            'players_per_group': config['group']['players-per-group'],
            'speed_cost': config['parameters']['speed-cost'],
            'num_demo_participants': config['demo']['number-of-participants'],
            'fundamental_price': config['parameters']['fundamental-price'],
            'initial_spread': config['parameters']['initial-spread'],
            'max_spread': config['parameters']['max-spread'],
            'initial_endowment': config['parameters']['initial-endowment'],
            'session_length': config['parameters']['session-length'],
            'app_sequence': ['hft_bcs']
            }

    except KeyError as e:
        raise e
        print('Failed to read custom configs %s.' % filename)
        print('Check keys in config file.')
    except: 
        print('Failed to read custom configs %s.' % filename)
    else:
        cfg_dir = os.path.join(os.getcwd(), config['files']['dir'], config['files']['folder'])
        all_files = find_all(cfg_dir, '.csv')
        for k, v in config['files']['investors'].items():
            label = 'investors' + '_' + k
            csv_name = collect.extract_name(v)
            if csv_name not in all_files:
                h = collect.headers(my_token) 
                data = collect.get(v, h)
                collect.write(data, cfg_dir, csv_name)
                print('Downloaded: %s.' % csv_name)
            path = os.path.join(cfg_dir, csv_name)
            custom_config.update({label: path})
        for k, v in config['files']['jumps'].items():
            label = 'jumps' + '_' + k
            csv_name = collect.extract_name(v)
            if csv_name not in all_files:
                h = collect.headers(my_token) 
                data = collect.get(v, h)
                collect.write(data, cfg_dir, csv_name)
                print('Downloaded: %s.' % csv_name)
            path = os.path.join(cfg_dir, csv_name)
            custom_config.update({label: path})
        print('Read custom configs %s.' % filename)
    return custom_config


def augment(session_configs):
    config_files = find_all(all_configs_dir, '.yaml')
    for cf in config_files:
        config_dict = read(cf)
        custom_config = create(config_dict, cf)
        session_configs.append(custom_config)
    return session_configs


