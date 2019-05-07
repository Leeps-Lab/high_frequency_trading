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
            'speed_unit_cost': 'speed_unit_cost',
            'default_role': 'default_role'
        }
    },
    checkpoint={
        'properties_to_serialize': (
            'subsession_id', 'market_id', 'id_in_market', 'player_id', 'delay', 
            'staged_bid', 'staged_offer', 'net_worth', 'cash', 'cost', 'tax_paid',
            'speed_cost', 'implied_bid', 'implied_offer'),
        'subproperties_to_serialize': {
            'trader_role': ('trader_model_name', ),
            'sliders': ('slider_a_x', 'slider_a_y', 'slider_a_z'),
            'orderstore': ('inventory', 'bid', 'offer'),
            'inventory': ('position', ),
            'market_facts': ('reference_price', 'best_bid', 'best_offer', 
                'signed_volume', 'e_best_bid', 'e_best_offer', 'e_signed_volume')
        }
     }
    )

environments = {
    'elo': elo
}
