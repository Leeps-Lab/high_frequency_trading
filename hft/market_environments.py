from collections import namedtuple

market_environment = namedtuple(
    'Environment', 'exogenous_events config_field_type fields_to_scale model_configuration')
market_environment.__new__.__defaults__ = (None, None, None)

# elo

elo = market_environment(
    exogenous_events=('investor_arrivals', ),
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
            'period_length': 'round_length',
            'auction_format': 'design',
        },
        'player': {
            'initial_endowment': 'cash',
            'technology_unit_cost': 'technology_unit_cost',
            'auction_format': 'design',
        }
    })

environments = {
    'elo': elo
}
