from channels import Group as CGroup, Channel
from collections import deque
import json
import time
import logging

log = logging.getLogger(__name__)

class  Broadcaster:

    flush_interval = 0.25 #seconds
    queues = {}
    flush_history = {}
    unbatchable_message_types = ('system_event', 'role_confirm', 'speed_confirm')


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
            self.flush_history[market_id] = time.time()
        # len(), append, pop are thread safe
        mq = self.queues[market_id]
        mq.append(message)
        now = time.time()
        time_since_flush =  now - self.flush_history[market_id]
        if  time_since_flush > self.flush_interval:
            num_msg_to_batch = len(mq)
            batched_messages = [mq.popleft().data for i in range(num_msg_to_batch)]
            json_msg = json.dumps({'type': 'batch', 'batch': batched_messages})
            self.broadcast_to_market(json_msg, market_id=market_id)
            self.flush_history[market_id] = now
            log.info('flushed broadcast queue %s messages', num_msg_to_batch)



        
