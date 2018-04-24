from channels import Group, Channel
from channels.sessions import channel_session
from .models import Player, Group as OtreeGroup, Investor
import json
import random
import datetime
import time

# Consumers for clients
# Connected to websocket.connect
def ws_connect(message, group_name):
    print('Player connected.')
    message.reply_channel.send({'accept': True})
    Group(group_name).add(message.reply_channel)


# Connected to websocket.receive
def ws_receive(message, group_name):
    group_id = group_name[5:]
    mygroup = OtreeGroup.objects.get(id=group_id)
    json_message = json.loads(message.content['text'])
    print(message.content)
    player = mygroup.get_player_by_id(json_message['id_in_group'])
    player.channel = message.reply_channel
    player.receive_from_client(json_message)

# Connected to websocket.disconnect
def ws_disconnect(message, group_name):
    Group(group_name).discard(message.reply_channel)


# Consumers for the investor
# Connected to websocket.connect
def ws_connect_inv(message, group_name):
    print('Investor connected.')
    message.reply_channel.send({'accept': True})

# Connected to websocket.receive
def ws_receive_inv(message, group_name):
    print('Investor here!')
    group_id = group_name[5:]
    investor = Investor.objects.create(group_id=group_id)
    investor.receive_from_consumer(message)


#  inverse consumer?? Works well.
def ws_send(message, channel):
    Channel(str(channel)).send(message)
