from collections import namedtuple

market_environment = namedtuple('Environment', 'exogenous_events config_field_type_and_scale model_configuration')
market_environment.__new__.__defaults__ = (None, None, None)

# elo

elo = market_environment(
    exogenous_events=('investor_arrivals', ),
    config_field_type_and_scale={
        'initial_endowment': (int, 1e4),
        'speed_cost': (int, 1e4),
    },
    model_configuration={
        'subsession': {
        #   key in configs : name on model
            'players_per_group': 'players_per_group',
            'period_length': 'round_length',
            'auction_format': 'design',
            'batch_length': 'batch_length',
        },
        'player': {
            'fundamental_price': 'fp',
            'initial_spread': 'spread',
            'initial_endowment': 'endowment',
            'speed_cost': 'speed_unit_cost',
            'max_spread': 'max_spread',
            'auction_format': 'design',
        }
    })

environments = {
    'elo': elo
}
