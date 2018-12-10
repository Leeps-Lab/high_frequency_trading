from channels import Group, Channel
from channels.generic.websockets import JsonWebsocketConsumer
from .models import (write_to_cache_with_version, get_cache_key, stop_exogenous, 
    Constants, Player, Investor, Group as OGroup )
from .client_messages import broadcast
import json
import logging
from django.core.cache import cache
from .decorators import timer
from .event_handlers import receive_trader_message, process_response
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

    @timer
    def raw_receive(self, message, group_id, player_id):
        try:
            message_content = json.loads(message.content['text'])
            player_data_key =  get_cache_key(player_id, 'player')
            player_data = cache.get(player_data_key)
            if player_data is None:
                log.warning('key %s returned none from cache.' % player_data_key)
                return
            player = player_data['model']
            event_type = message_content['type']
            if event_type in Constants.trader_events:
                trader = receive_trader_message(player_id, event_type, **message_content)
                process_response(trader)
            else:
                handler_name = Constants.player_handlers[event_type]
                handler = getattr(player, handler_name)
                handler(**message_content)
        except Exception as e:
            log.exception('player %s: error processing message, ignoring. %s:%s', player_id, message_content, e)

    def raw_disconnect(self, message, group_id, player_id):
        log.info('Player %s disconnected from Group %s.' % (player_id, group_id))
        Group(group_id).discard(message.reply_channel)
        


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
        investor.receive_from_consumer(msg)

    def raw_disconnect(self, message, group_id):
        log.info('Investor disconnected from Group %s.' % group_id)


class JumpConsumer(JsonWebsocketConsumer):

    def raw_connect(self, message, group_id):
        log.info('Jump is connected to Group %s.' % group_id)

    def raw_receive(self, message, group_id):
        msg = json.loads(message.content['text'])
        group = OGroup.objects.get(id=group_id)
        group.jump_event(msg)

    def raw_disconnect(self, message, group_id):
        log.info('Jump disconnected from Group %s.' % group_id)


class Stop(JsonWebsocketConsumer):

    def raw_connect(self, message):
        pass

    def raw_receive(self, message):
        log.info('received stop investor & jumps signal..')
        stop_exogenous()


    def raw_disconnect(self, message):
        pass