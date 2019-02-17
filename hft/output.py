from otree.api import models
from otree.db.models import Model, ForeignKey
import datetime
import os
import csv

class HFTPlayerStateRecord(Model):

    timestamp = models.DateTimeField(auto_now_add=True)
    subsession_id = models.StringField()
    player_id = models.IntegerField()
    market_id = models.StringField()
    role =  models.StringField()
    speed_on = models.BooleanField()
    trigger_event_type = models.StringField()
    event_no = models.IntegerField()
    inventory = models.IntegerField()
    orderstore = models.StringField()
    bid = models.IntegerField(blank=True)
    offer = models.IntegerField(blank=True)

    def from_event_and_player(self, event_dict, player):
        for field in ('role', 'market_id', 'speed_on', 'inventory', 'bid', 
            'offer', 'orderstore'):
            setattr(self, field, getattr(player, field))  
        self.player_id = int(player.id)
        self.trigger_event_type = str(event_dict['event'])  
        self.event_no = int(event_dict['reference_no'])
        self.subsession_id = str(event_dict['subsession_id'])
        return self

class HFTEventRecord(Model):
    
    subsession_id= models.StringField()
    market_id = models.StringField()
    timestamp = models.DateTimeField(auto_now_add=True)
    event_no = models.IntegerField()
    event_source = models.StringField()
    event_type = models.StringField()
    original_message = models.StringField()
    attachments = models.StringField()
    outgoing_messages = models.StringField()

    def from_event(self, event_dict):
        self.subsession_id = str(event_dict['subsession_id'])
        self.market_id = str(event_dict['market_id'])
        self.event_no = int(event_dict['reference_no'])
        self.event_type = str(event_dict['event_type'])
        self.event_source = str(event_dict['event_source'])
        self.all_keys = str(event_dict)
        self.outgoing_messages = str(event_dict['outgoing_messages'])
        return self


class HFTInvestorRecord(Model):

    timestamp = models.DateTimeField(auto_now_add=True)
    exchange_timestamp = models.BigIntegerField()
    subsession_id= models.StringField()
    market_id = models.StringField()
    order_token = models.StringField()
    status = models.StringField()
    buy_sell_indicator = models.StringField()
    price = models.IntegerField()

    def from_event(self, event):
        self.subsession_id = str(event_dict['subsession_id'])
        self.market_id = str(event_dict['market_id'])       
        self.status = event.event_type
        self.order_token = event.message.data.order_token
        if 'buy_sell_indicator' in event.message.data:
            self.buy_sell_indicator = event.message.data.buy_sell_indicator
        else:
            self.buy_sell_indicator = event.message.data.order_token[4]
        if 'price' in event.message:
            self.price = event.message.data.price
        else:
            self.price = event.message.data.execution_price
        self.exchange_timestamp = event.message.data.timestamp
        return self




results_foldername = 'results'
base_session_foldername = '{timestamp:%Y%m%d_%H:%M}_session_{session_code}'  
base_subsession_foldername = 'subsession_{subsession_id}_round_{round_no}'                         

base_filename = 'market_{market_id}_record_type_{record_class}_subsession_{subsession_id}.csv'

csv_headers = {
    'HFTEventRecord': ['event_no','timestamp', 'subsession_id', 'market_id', 
        'event_source', 'event_type', 'original_message', 'attachments', 'outgoing_messages'],
    'HFTPlayerStateRecord': ['timestamp', 'session_id', 'subsession_id', 'player_id', 'market_id', 'role',
        'speed_on', 'trigger_event_type', 'event_no', 'inventory', 'orderstore', 'bid',
        'offer'],
    'HFTInvestorRecord': ['timestamp', 'exchange_timestamp', 'subsession_id', 
        'market_id', 'status', 'buy_sell_indicator', 'price', 'order_token']
}

def close_trade_session(trade_session):
    current_session_code = trade_session.subsession.session.code
    current_subsession_id = trade_session.subsession.id
    markets_ids_in_session = trade_session.market_state.keys()
    current_round_number = trade_session.subsession.round_number
    _collect_and_dump(current_session_code, current_subsession_id, markets_ids_in_session,
        current_round_number)

def _collect_and_dump(session_code, subsession_id:int, market_ids:list, round_no:int):  
    if results_foldername not in os.listdir(os.getcwd()):
        os.mkdir(results_foldername)
    session_foldernames = [x for x in os.listdir(results_foldername) 
        if x.endswith(session_code)]
    if len(session_foldernames) > 1:
        raise ValueError('multiple matching folders in %s' % session_foldernames)
    elif not session_foldernames:
        now = datetime.datetime.now()
        session_foldername = base_session_foldername.format(timestamp=now, 
            session_code=session_code)
        os.mkdir(os.path.join(results_foldername,session_foldername))
    else:
        session_foldername = session_foldernames.pop()   
    session_directory = os.path.join(results_foldername, session_foldername) 
    subsession_foldername = base_subsession_foldername.format(subsession_id=subsession_id, 
        round_no=round_no)
    if subsession_foldername not in os.listdir(session_directory):
        os.mkdir(os.path.join(results_foldername, session_foldername, 
            subsession_foldername))
    for record_class in HFTEventRecord, HFTPlayerStateRecord, HFTInvestorRecord:
        all_records = record_class.objects.filter(subsession_id=subsession_id)
        for market_id in market_ids:
            market_records = all_records.filter(market_id=str(market_id))
            filename = base_filename.format(market_id=market_id, record_class=
                record_class.__name__, subsession_id=subsession_id)
            path = os.path.join(session_directory, subsession_foldername, filename)
            with open(path, 'w') as f:
                fieldnames = csv_headers[record_class.__name__]
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                for row in market_records:
                    writer.writerow(row.__dict__)

def _elo_fields(player, subject_state):
    player.best_bid = subject_state.best_quotes['B']
    player.best_offer = subject_state.best_quotes['S']
    if subject_state.distance_from_best_quote is not None:
        player.distance_from_bid = subject_state.distance_from_best_quote['B']
        player.distance_from_offer = subject_state.distance_from_best_quote['S']
    if subject_state.latent_quote is not None:
        player.latent_bid = subject_state.latent_quote['B']
        player.latent_offer = subject_state.latent_quote['S']
    if subject_state.sliders is not None:
        player.sliders = str(subject_state.sliders)
    player.orderstore = str(subject_state.orderstore)
    player.bid = subject_state.orderstore.bid
    player.offer = subject_state.orderstore.offer
    player.market_id = str(subject_state.market_id)

def from_trader_to_player(player, subject_state, post=_elo_fields):
    for field in subject_state.__slots__:
        if hasattr(player, field):
            setattr(player, field, getattr(subject_state, field))
    if post:
        post(player, subject_state)
    player.save()
    return player

