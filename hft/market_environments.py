from collections import namedtuple

market_environment = namedtuple(
    'Environment', 
    'exogenous_events config_field_type fields_to_scale model_configuration checkpoint export_meta')
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
        'speed_unit_cost': 10000
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
        'trader': {
            'events_to_capture': ('speed_change', 'role_change', 'slider', 
                'market_start', 'market_end', 'A', 'U', 'C', 'E'),
            'properties_to_serialize': (
                'subsession_id', 'market_id', 'id_in_market', 'player_id', 'delay', 
                'staged_bid', 'staged_offer', 'net_worth', 'cash', 'cost', 'tax_paid',
                'speed_cost', 'implied_bid', 'implied_offer', 'best_bid_except_me',
                'best_offer_except_me', 'executed_price', 'buy_sell_indicator'),
            'subproperties_to_serialize': {
                'trader_role': ('trader_model_name', ),
                'sliders': ('slider_a_x', 'slider_a_y', 'slider_a_z'),
                'orderstore': ('inventory', 'bid', 'offer'),
                'inventory': ('position', ),
                'market_facts': (
                    'reference_price', 'best_bid', 'best_offer', 
                    'signed_volume', 'e_best_bid', 'e_best_offer', 'e_signed_volume',
                    'next_bid', 'next_offer', 'volume_at_best_bid', 'volume_at_best_offer')
            }
        },
        'market': {
            'events_to_capture': ('Q', 'E', 'Z', 'market_start', 'market_end',
                'external_feed'), 
            'properties_to_serialize': ('subsession_id', 'market_id', 'clearing_price', 'transacted_volume'),
            'subproperties_to_serialize': {
                'bbo': ('best_bid', 'best_offer', 'next_bid', 'next_offer', 
                        'volume_at_best_bid', 'volume_at_best_offer'),
                'external_feed': ('e_best_bid', 'e_best_offer', 'e_signed_volume'),
                'signed_volume': ('signed_volume', ),
                'reference_price': ('reference_price', )
            }
        },
        'inv': {
            'events_to_capture': ('A', 'E', 'L'),
            'properties_to_serialize': (
                'subsession_id', 'market_id', 'id_in_market', 'player_id', 'delay', 
                'staged_bid', 'staged_offer', 'net_worth', 'cash', 'midpoint_peg', 'peg_price', 'peg_state'),
            'subproperties_to_serialize': {
                'orderstore': ('inventory', 'bid', 'offer'),
                'trader_role': ('trader_model_name', ),
            }            
        }
    },
    # export_meta={
    #     'trader': 
    # }
)


environments = {
    'elo': elo
}
