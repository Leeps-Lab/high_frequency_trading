from otree.api import models
from otree.db.models import Model, ForeignKey
import datetime
import os
import csv
from .utility import from_trader_to_player


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

    def from_event_and_player(self, event, player):
        for field in ('role', 'market_id', 'speed_on', 'inventory', 'bid', 
            'offer', 'orderstore'):
            setattr(self, field, getattr(player, field))  
        self.trigger_event_type = str(event.event_type)  
        self.event_no = int(event.reference_no)
        self.session_id = int(player.session.id)
        self.subsession_id = str(player.subsession.id)
        self.player_id = int(player.id)
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

    def from_event(self, event):
        self.subsession_id = str(event.attachments['subsession_id'])
        self.market_id = str(event.attachments['market_id'])
        self.event_no = int(event.reference_no)
        self.event_type = str(event.event_type)
        self.event_source = str(event.event_source)
        self.original_message = str(event.message)
        self.attachments = str(event.attachments)
        self.outgoing_messages = str(event.outgoing_messages)
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
        'offer']
}

def close_trade_session(trade_session):
    current_session_code = trade_session.subsession.session.code
    current_subsession_id = trade_session.subsession.id
    markets_ids_in_session = trade_session.market_state.keys()
    current_round_number = trade_session.subsession.round_number
    _collect_and_dump(current_session_code, current_subsession_id, markets_ids_in_session,
        current_round_number)

def _collect_and_dump(session_code, subsession_id:int, market_ids:list, round_no:int):  
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
    for record_class in HFTEventRecord, HFTPlayerStateRecord:
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


def hft_trader_checkpoint(player_id, subject_state, event):
    player = from_trader_to_player(player_id, subject_state)
    player_record = HFTPlayerStateRecord().from_event_and_player(event, player)
    player_record.save()

def hft_event_checkpoint(event):
    event_record = HFTEventRecord().from_event(event)
    event_record.save()

