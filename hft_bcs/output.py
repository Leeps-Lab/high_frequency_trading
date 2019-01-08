from otree.api import models
from otree.db.models import Model, ForeignKey
import datetime
import os
import csv
from .utility import from_trader_to_player


class HFTPlayerStateRecord(Model):

    timestamp = models.DateTimeField(auto_now_add=True)
    session_id = models.IntegerField()
    player_id = models.IntegerField()
    market = models.IntegerField()
    role =  models.StringField()
    speed_on = models.BooleanField()
    trigger_event_type = models.StringField()
    event_no = models.IntegerField()
    inventory = models.IntegerField()
    orderstore = models.StringField()
    bid = models.IntegerField(blank=True)
    offer = models.IntegerField(blank=True)

    def from_event_and_player(self, event, player):
        for field in ('role', 'market', 'speed_on', 'inventory', 'bid', 
            'offer', 'orderstore'):
            setattr(self, field, getattr(player, field))  
        self.trigger_event_type = str(event.event_type)  
        self.event_no = int(event.reference_no)
        self.session = player.session.id
        self.player_id = player.id
        self.save()
        return self

class HFTEventRecord(Model):
    
    subsession_id= models.IntegerField()
    market_id = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    event_no = models.IntegerField()
    event_source = models.StringField()
    event_type = models.StringField()
    original_message = models.StringField()
    attachments = models.StringField()
    outgoing_messages = models.StringField()

    def from_event(self, event):
        self.subsession_id = event.attachments['subsession_id']
        self.event_no = event.reference_no
        self.event_type = event.event_type
        self.event_source = event.event_source
        self.original_message = event.message
        self.attachments = event.attachments
        self.outgoing_messages = event.outgoing_messages
        self.save()
        return self

results_foldername = 'results'
session_foldername = '{timestamp}_session_{session_code}'  
base_subsession_foldername = 'subsession_{subsession_id}_round_{round_no}'                         

base_filename = 'market_{market_id}_record_type_{record_class}'

csv_headers = {
    'HFTEventRecord': ['event_no','timestamp', 'subsession_id', 'market_id', 
        'event_source', 'event_type', 'original_message', 'attachments', 'outgoing_messages'],
    'HFTPlayerStateRecord': ['timestamp', 'session_id', 'player_id', 'market', 'role',
        'speed_on', 'trigger_event_type', 'event_no', 'inventory', 'orderstore', 'bid',
        'offer']
}

def collect_and_dump(session_code, subsession_id:int, market_ids:list, round_no:int):  
    if not any(filter(lambda x: x.endswith(session_code), 
        os.listdir(results_foldername))):
        now = datetime.datetime.now()
        os.mkdir(base_subsession_foldername.format(timestamp=now, session_code=session_code))
    session_directory = os.path.join(results_foldername, session_foldername) 
    subsession_foldername = base_subsession_foldername.format(subsession_id=subsession_id, 
        round_no=round_no)
    if subsession_foldername not in os.listdir(session_directory):
        os.mkdir(subsession_foldername)
    for record_class in HFTEventRecord, HFTPlayerStateRecord:
        all_records = record_class.objects.get(subsession_id=subsession_id)
        for market_id in market_ids:
            market_records = all_records.filter(market_id=market_id)
            filename = base_filename.format(market_id=market_id, record_class=
                record_class.__name__)
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
