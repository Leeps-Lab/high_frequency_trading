from channels import Group as CGroup, Channel
from collections import deque
import json
import time
import logging
from twisted.internet.task import LoopingCall

log = logging.getLogger(__name__)

class  Broadcaster:

    flush_interval = 0.25 #seconds
    unbatchable_message_types = ('system_event', 'role_confirm', 'speed_confirm',
        'slider_confirm')

    def __init__(self):
        self.queues = {}
        LoopingCall(self.flush).start(self.flush_interval)

    def broadcast(self, message, batch=False):
        if batch and message.type not in self.unbatchable_message_types:
            self.append(message)
        else:
            self.broadcast_to_market(message)

    @staticmethod
    def broadcast_to_market(message, market_id=None):
        if market_id is None:
            market_id = message.market_id
        channel_group = CGroup(str(market_id))
        json_msg = message
        if not isinstance(json_msg, str):
            json_msg = message.to_json()
        channel_group.send({"text": json_msg})

    def append(self, message):
        market_id = message.market_id
        if market_id not in self.queues:
            self.queues[market_id] = deque()
        # len(), append, pop are thread safe
        mq = self.queues[market_id]
        mq.append(message)

    def flush(self):
        for market_id, mq in self.queues.items():
            num_msg_to_batch = len(mq)
            if num_msg_to_batch == 0:
                continue
            print('flushing queue for market ', market_id)
            batched_messages = [mq.popleft().data for i in range(num_msg_to_batch)]
            json_msg = json.dumps({'type': 'batch', 'batch': batched_messages})
            self.broadcast_to_market(json_msg, market_id=market_id)
