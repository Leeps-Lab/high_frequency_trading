from channels import Group, Channel
from channels.generic.websockets import JsonWebsocketConsumer
from .models import Player, Investor, Group as OGroup
import json
import logging

log = logging.getLogger(__name__)

class SubjectConsumer(JsonWebsocketConsumer):

    def raw_connect(self, message, group_id, player_id):
        Group(group_id).add(message.reply_channel)
        self.connect(message, group_id, player_id)

    def connect(self, message, group_id, player_id):
        player = Player.objects.get(id=player_id)
        log.info('Player %s is connected to Group %s with in-group id %s.' % (
            player_id, group_id, player.id_in_group))
        player.channel = message.reply_channel
        player.save()

    def raw_receive(self, message, group_id, player_id):
        msg = json.loads(message.content['text'])
        player = Player.objects.get(id=player_id)
        player.receive_from_client(msg)

    def raw_disconnect(self, message, group_id, player_id):
        log.info('Player %s  disconnected from Group %s.' % (player_id, group_id))
        Group(group_id).discard(message.reply_channel)
        group = OGroup.objects.get(id=group_id)
        group.subsession.player_dropped(player_id)
        


class InvestorConsumer(JsonWebsocketConsumer):

    def raw_connect(self, message, group_id):
        log.info('Investor is connected to Group %s.' % group_id)
        self.connect(group_id)

    def connect(self, group_id):
        investor = Investor.objects.create(group_id=group_id)
        investor.save()

    def raw_receive(self, message, group_id):
        msg = json.loads(message.content['text'])
        investor = Investor.objects.get(group_id=group_id)
        investor.receive_from_consumer(msg['side'])

    def raw_disconnect(self, message, group_id):
        log.info('Investor disconnected from Group %s.' % group_id)


class JumpConsumer(JsonWebsocketConsumer):

    def raw_connect(self, message, group_id):
        log.info('Jump is connected to Group %s.' % group_id)

    def raw_receive(self, message, group_id):
        msg = json.loads(message.content['text'])
        group = OGroup.objects.get(id=group_id)
        group.jump_event(msg['price'])

    def raw_disconnect(self, message, group_id):
        log.info('Jump disconnected from Group %s.' % group_id)