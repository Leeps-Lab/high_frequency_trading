from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
from jsonfield import JSONField

from . import exchange


author = 'LEEPS Lab UCSC'

doc = """
Your app description
"""


class Constants(BaseConstants):
    name_in_url = 'oTree_HFT_CDA'
    players_per_group = 2
    num_rounds = 5


class Subsession(BaseSubsession):

    def creating_session(self):
        for i, group in enumerate(self.get_groups()):
            group.port = 9000 + i
            group.json = {
                "messages": [],
            }
            group.save()
        

class Group(BaseGroup):
    port = models.IntegerField()
    json = JSONField()

    def connect_to_exchange(self):
        exchange.connect(self, '127.0.0.1', self.port)

    def disconnect_from_exchange(self):
        exchange.disconnect(self, '127.0.0.1', self.port)

    def send_message(self, msg):
        conn = exchange.connect(self, '127.0.0.1', self.port, wait_for_connection=True).connection
        conn.sendMessage(msg)

    def recv_message(self, msg):
        self.json['messages'].append(msg)
        self.save()

    def save(self, *args, **kwargs):
        """
        BUG: Django save-the-change, which all oTree models inherit from,
        doesn't recognize changes to JSONField properties. So saving the model
        won't trigger a database save. This is a hack, but fixes it so any
        JSONFields get updated every save. oTree uses a forked version of
        save-the-change so a good alternative might be to fix that to recognize
        JSONFields (diff them at save time, maybe?).
        """
        super().save(*args, **kwargs)
        if self.pk is not None:
            json_fields = {}
            for field in self._meta.get_fields():
                if isinstance(field, JSONField):
                    json_fields[field.attname] = getattr(self, field.attname)
            self.__class__._default_manager.filter(pk=self.pk).update(**json_fields)


class Player(BasePlayer):
    msg = models.StringField()