
from django.db.models import Model, ForeignKey
from otree.api import models
import csv
#from otree.common_internal import random_chars_8
from .trader import InvestorFactory
import logging

log = logging.getLogger(__name__)


class ExogenousEventModelFactory:

    @staticmethod
    def get_model(event_type_name, market):
        if event_type_name == 'investor_arrivals':
            return InvestorFactory.get_model(market)
        else:
            log.warning('no in-memory model for event type %s' % event_type_name)


class ExogenousEventFile(Model):

    upload_time = models.DateTimeField(auto_now_add=True)
    upload_name = models.StringField()
    code = models.CharField(primary_key=True, editable=False, 
        null=False) #delete default=random_chars_8
    record_type = models.StringField()


class CSVRowMixIn:
    
    @classmethod
    def from_csv_row(cls, csv_row:list, csv_headers:list, **kwargs):
        instance = cls.objects.create(**kwargs)

        for ix, fieldname in enumerate(csv_headers):

            fieldvalue = csv_row[ix]
            setattr(instance, fieldname, fieldvalue)

           
        return instance

class ExogenousOrderRecord(Model, CSVRowMixIn):

    submitted_file = ForeignKey(ExogenousEventFile, on_delete=models.CASCADE)
    arrival_time = models.FloatField()
    market_id_in_subsession = models.StringField()
    price = models.IntegerField()
    time_in_force = models.IntegerField()
    buy_sell_indicator = models.StringField()


class ExternalFeedRecord(Model, CSVRowMixIn):

    submitted_file = ForeignKey(ExogenousEventFile, on_delete=models.CASCADE)
    arrival_time = models.FloatField()
    market_id_in_subsession = models.StringField()
    e_best_bid = models.IntegerField()
    e_best_offer = models.IntegerField()
    e_signed_volume = models.FloatField()


def handle_exogenous_event_file(filename, filelike, record_cls, record_type):
    if None in (filename, filelike):
        raise Exception('null input {}:{}'.format(filename, filelike))
    if not isinstance(filename, str):
        try:    
            filename = str(filename)
        except:     
            raise Exception('invalid filename {}'.format(filename))
    if not len(filename):
        raise Exception('filename should have at least one character %s' % filename) 
    if ExogenousEventFile.objects.filter(upload_name=filename).exists():
        log.warning('event file: {} already in db, overwriting.'.format(filename))
        file_record = ExogenousEventFile.objects.get(upload_name=filename)
        file_record.delete()
        # should cascade
        if record_cls.objects.filter(submitted_file=file_record).exists():
            raise Exception('exogenous event record delete and cascade failed.')
    reader = csv.reader(filelike)
    rows = [row for row in reader]
    headers = rows[0]
    file_record = ExogenousEventFile.objects.create(
        upload_name=filename, record_type=record_type)
    for row in rows[1:]:
        # Edge case to handle if csv reader is trying to read an empty row
        if len(row) > 0:
            ex_order = record_cls.from_csv_row(row, 
                headers, submitted_file=file_record)
            ex_order.save()

def get_exogenous_event_queryset(event_type, filename):
    queryset_info = get_exg_query_set_meta(event_type)
    event_file_model_cls = queryset_info['event_file_model']
    event_model_cls = queryset_info['event_model']
    event_file_model = event_file_model_cls.objects.get(upload_name=filename)
    queryset = event_model_cls.objects.filter(submitted_file=event_file_model).order_by(
            queryset_info['order_by'])
    return queryset

exg_event_query_meta = {
    'investor_arrivals': {
        'event_model': ExogenousOrderRecord, 'event_file_model': ExogenousEventFile,
        'order_by': 'arrival_time'},
    'external_feed': {
        'event_model': ExternalFeedRecord, 'event_file_model': ExogenousEventFile,
        'order_by': 'arrival_time'}}
def get_exg_query_set_meta(event_type, source=exg_event_query_meta):
    try:
        return source[event_type]
    except KeyError:
        raise Exception('invalid event type %s' % event_type)

def get_filecode_from_filename(event_type, filename):
    m = get_exg_query_set_meta(event_type)
    event_file_model_cls = m['event_file_model']
    print(filename)
    event_file_model = event_file_model_cls.objects.get(upload_name=filename)
    return event_file_model.code
