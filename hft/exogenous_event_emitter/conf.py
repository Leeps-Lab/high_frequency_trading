import os
from urllib.parse import urlparse

ws_client_confs = {   
    'investor_arrivals': {
        'columns': ['arrival_time', 'market_id_in_subsession', 'price', 'time_in_force',
            'buy_sell_indicator'],
        'table_name': 'hft_exogenousorderrecord',
        'filter_on': 'submitted_file_id'
    },
    'external_feed': {
        'columns': ['arrival_time', 'market_id_in_subsession', 'e_best_bid', 
            'e_best_offer', 'e_signed_volume'],
        'table_name': 'hft_externalfeedrecord',
        'filter_on': 'submitted_file_id'
    }
}

def get_ws_confs(type_code, source=ws_client_confs):
    try:
        return ws_client_confs[type_code]
    except KeyError:
        raise Exception('invalid type code %s' % type_code)

database_url = os.environ.get('DATABASE_URL')
parsed_url = urlparse(database_url)
db_creds = {'dbname': parsed_url.path[1:], 'user': parsed_url.username,
    'password': parsed_url.password, 'host': parsed_url.hostname}
