from collections import namedtuple

market_environment = namedtuple(
    'Environment', 'exogenous_events config_field_type fields_to_scale model_configuration')
market_environment.__new__.__defaults__ = (None, None, None)

# elo

elo = market_environment(
    exogenous_events=('investor_arrivals', 'external_feed'),
    config_field_type={
        'initial_endowment': int,
        'speed_cost': float
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
    })

environments = {
    'elo': elo
}
