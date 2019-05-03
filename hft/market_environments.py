from collections import namedtuple

market_environment = namedtuple(
    'Environment', 
    'exogenous_events config_field_type fields_to_scale model_configuration checkpoint')
market_environment.__new__.__defaults__ = (None, None, None, None, None)

# elo

elo = market_environment(
    exogenous_events=('investor_arrivals', 'external_feed'),
    config_field_type={
        'initial_endowment': int,
        'speed_cost': float,
        'technology_unit_cost': float
    },
    fields_to_scale={
        'initial_endowment': 10000,
        'technology_unit_cost': 10000
    },
    model_configuration={  
        'subsession': {
        #   key in configs: attribute on model
            'session_duration': 'session_duration',
            'auction_format': 'auction_format',
        },
        'player': {
            'initial_endowment': 'cash',
            'technology_unit_cost': 'technology_unit_cost',
            'auction_format': 'auction_format',
        }
    },
    checkpoint={
        'subproperties_to_serialize': {
            'sliders': ('slider_a_x', 'slider_a_y', 'slider_a_z'),
            'orderstore': ('inventory', 'bid', 'offer'),
        },
        'record_model_code': '1'
    }
    )

environments = {
    'elo': elo
}
