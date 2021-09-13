from channels import Group, Channel
from channels.generic.websockets import JsonWebsocketConsumer
from .decorators import timer
from .dispatcher import ELODispatcher
from .models import Player
from .output import TraderRecord
import json
import logging

log = logging.getLogger(__name__)

class SubjectConsumer(JsonWebsocketConsumer):

    def raw_connect(self, message, subsession_id, group_id, player_id):
        player = Player.objects.get(id=player_id)
        Group(player.market_id).add(message.reply_channel)
        self.connect(message, subsession_id, group_id, player_id)

    def connect(self, message, subsession_id, group_id, player_id):
        player = Player.objects.get(id=player_id)
        log.info('player %s connected. subsession %s, market %s' % (
            player_id, subsession_id, group_id))
        player.channel = message.reply_channel
        player.save()

    def raw_receive(self, message, subsession_id, group_id, player_id):
        
        try:
            content = json.loads(message.content['text'])
            if 'avgLatency' in content:
                player = Player.objects.get(id=player_id)
       
                TraderRecord.objects.filter(subsession_id=subsession_id,
                    market_id=group_id, player_id=player_id).update(avgLatency = content['avgLatency'], maxLatency = content['maxLatency'])

            else:
                ELODispatcher.dispatch('websocket', message, subsession_id=subsession_id,
                    market_id=group_id, player_id=player_id)
        except Exception as e:
            log.exception('player %s: error processing message, ignoring. %s:%s', 
                player_id, message.content, e)

    def raw_disconnect(self, message, subsession_id, group_id, player_id):
        player = Player.objects.get(id=player_id)
        Group(player.market_id).add(message.reply_channel)      

class ExogenousEventConsumer(JsonWebsocketConsumer):

    def raw_receive(self, message, subsession_id):
        try:
            ELODispatcher.dispatch('websocket', message, subsession_id=subsession_id,
                player_id=0)
        except Exception as e:
            log.exception('error processing investor arrival, ignoring. %s:%s', message.content, e)
