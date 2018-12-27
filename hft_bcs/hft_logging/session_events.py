import csv
from ..utility import nanoseconds_since_midnight as labtime
import os
from datetime import datetime
from .row_formatters import *

author = 'hasan ali demirci'

# TODO: move this to redis.

logs_folder = 'hft_bcs/hft_logging/market_events/'

class SessionEvents:

    dispatch = {
        'stage enter': format_senter,
        'stage replace': format_sreplace,
        'stage cancel': format_scancel,
        'confirm enter': format_center,
        'confirm replace': format_creplace,
        'confirm cancel': format_ccancel,
        'confirm execution': format_cexec,
        'orders in market': format_orders,
    }

    filename = ('{timestamp}_design_{subsession.design}_players_per_group_'
        '{subsession.players_per_group}_round_{subsession.round_number}.csv')

    def __init__(self, subsession=None):
        """
        this will be called only once
        at startup, then will change save
        path at each round
        """
        self.backup = list()
        self.raw_logs = list()
        self.string_logs = list()
        self.columns = ['time', 'group', 'player', 'event', 'context']
        self.path = None
        self.subsession = subsession
        self.round_start = labtime()

    def __call__(self, subsession):
        self.backup = list()
        self.raw_logs = list()
        self.string_logs = list()
        self.round_start = labtime()
        self.set_dump_path(subsession)
    
    def set_dump_path(self, subsession):
        now = datetime.now().strftime('%Y-%m-%d_%H-%M')
        filename = self.filename.format(timestamp=now, subsession=subsession)
        self.path = os.path.join(logs_folder, filename)

    def push(self, processor, **kwargs):
        kwargs['round_start'] = self.round_start
        raw_log = processor(**kwargs)
        self.raw_logs.append(raw_log)

    def form(self, row):
        out = row
        if isinstance(row['context'], dict):
            event = row['event']
            out = self.__class__.dispatch[event](row)
        return out

    def convert(self):
        self.string_logs = [self.form(row) for row in self.raw_logs]
        self.backup.extend(self.raw_logs)
        self.raw_logs = list()

    def dump(self, header=False):
        with open(self.path, 'a') as f:
            writer = csv.DictWriter(f, self.columns)
            if header:
                writer.writeheader()
            writer.writerows(self.string_logs)

log_events = SessionEvents()