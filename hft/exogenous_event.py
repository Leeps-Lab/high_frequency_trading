
from otree.db.models import Model, ForeignKey
from otree.api import models
import csv
from otree.common_internal import random_chars_8
import logging
from .investor import InvestorFactory

log = logging.getLogger(__name__)


class ExogenousEventModelFactory:

    @staticmethod
    def get_message(event_type_name, *args, **kwargs):
        if event_type_name == 'investor_arrivals':
            return InvestorFactory(*args, **kwargs)
        else:
            raise Exception('invalid message source: %s' % message_source)


class ExogenousOrderFile(Model):

    upload_time = models.DateTimeField(auto_now_add=True)
    upload_name = models.StringField()
    code = models.CharField(primary_key=True, default=random_chars_8, editable=False, 
        null=False)

class ExogenousOrderRecord(Model):

    submitted_file = ForeignKey(ExogenousOrderFile, on_delete=models.CASCADE)
    arrival_time = models.FloatField()
    market_id_in_subsession = models.StringField()
    price = models.IntegerField()
    time_in_force = models.IntegerField()
    buy_sell_indicator = models.StringField()

    @classmethod
    def from_csv_row(cls, csv_row:list, csv_headers:list, **kwargs):
        instance = cls.objects.create(**kwargs)
        for ix, fieldname in enumerate(csv_headers):
            fieldvalue = csv_row[ix]
            setattr(instance, fieldname, fieldvalue)
        return instance

def handle_investor_file(filename, filelike):
    if None in (filename, filelike):
        raise Exception('null input {}:{}'.format(filename, filelike))
    if not isinstance(filename, str):
        try:    
            filename = str(filename)
        except:     
            raise Exception('invalid filename {}'.format(filename))
    if not len(filename):
        raise Exception('filename should have at least one character %s' % filename) 
    if ExogenousOrderFile.objects.filter(upload_name=filename).exists():
        log.warning('investor file: {} already in db, overwriting.'.format(filename))
        file_record = ExogenousOrderFile.objects.get(upload_name=filename)
        file_record.delete()
        # should cascade
        if ExogenousOrderRecord.objects.filter(submitted_file=file_record).exists():
            raise Exception('investor file record delete and cascade failed.')
    reader = csv.reader(filelike)
    rows = [row for row in reader]
    headers = rows[0]
    file_record = ExogenousOrderFile.objects.create(upload_name=filename)
    for row in rows[1:]:
        ex_order = ExogenousOrderRecord.from_csv_row(row, 
            headers, submitted_file=file_record)
        ex_order.save()


def get_exogenous_event_queryset(event_type, filename):
    try:
        queryset_info = exogenous_event_queryset[event_type]
        event_file_model_cls = queryset_info['event_file_model']
        event_model_cls = queryset_info['event_model']
        event_file_model = event_file_model_cls.objects.get(upload_name=filename)
        queryset = event_model_cls.objects.filter(submitted_file=event_file_model).order_by(
                queryset_info['order_by'])
    except KeyError or not queryset:
        raise Exception('{}:{} not found'.format(event_type, filename))
    else:
        return queryset

exogenous_event_queryset = {
    'investor_arrivals': {'event_model': ExogenousOrderRecord, 'event_file_model': ExogenousOrderFile,
        'order_by': 'arrival_time'}
}

