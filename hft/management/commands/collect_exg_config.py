"""
simple script to load configs.
"""
import logging
import os
from django.core.management.base import BaseCommand
from hft.exogenous_event import handle_exogenous_event_file
from hft.views import ExogenousOrderUploadView, ExternalFeedUploadView


INVESTORS_DIR = 'session_config/exogenous_events/investors'
EXTERNAL_FEED_DIR = 'session_config/exogenous_events/external_feed'


log = logging.getLogger(__name__)


exogenous_event_meta = [(INVESTORS_DIR, 'investor_arrivals', ExogenousOrderUploadView),
                        (EXTERNAL_FEED_DIR, 'external_feed', ExternalFeedUploadView)]


class Command(BaseCommand):
    help = 'read/store external feed/order flow configuration from filesystem.'

    def handle(self, *args, **kwargs):
        # assume all files under dir are of the same type.
        for source_dir, event_type, record_cls in exogenous_event_meta:
            for filename in os.listdir(source_dir):
                filepath = os.path.join(os.getcwd(), source_dir, filename)
                with open(filepath) as f:
                    handle_exogenous_event_file(filename, f, record_cls.record_cls,
                                                event_type)
                    log.info(f'read [{event_type}] events @ [{filepath}].')
