from .market_fact import FactTimer
from itertools import count
from math import ceil
import time
import logging

log = logging.getLogger(__name__)

class Subscription:

    counter = count(1, 1)

    def __init__(self, subscription_name, subscriber_id, unit_cost):
        self.id = next(self.__class__.counter)
        self.timer = FactTimer()
        self.__active = False
        self.unit_cost = unit_cost
        self.__uninvoiced_time = 0
        self.subscriber_id = subscriber_id
        self.name = subscription_name
    
    @property
    def is_active(self):
        return self.__active
    
    @property
    def uninvoiced_time(self):
        return self.__uninvoiced_time

    def activate(self):
        self.timer.step()
        if self.__active is False:
            self.__active = True
            log.debug('subscription activated, subscriber %s, unit cost: %s.' % (
                self.subscriber_id, self.unit_cost))
        else:
            log.warning('already active %s' % self)

    def deactivate(self):
        self.timer.step()
        self.__active = False
        self.__uninvoiced_time += round(self.timer.time_since_previous_step, 3)
        log.debug('subscriber %s: uninvoiced subscription time: %s sec.' % (
                   self.subscriber_id, self.__uninvoiced_time))

    def invoice(self):
        if self.is_active:
            self.deactivate()
        amount = round(self.__uninvoiced_time * self.unit_cost, 2) 
        # so minimum increment is a second
        log.debug('subscriber %s: uninvoiced time %s --> \
invoiced amount %s, unit cost: %s.' % (self.subscriber_id, self.__uninvoiced_time,
            amount, self.unit_cost))
        self.__uninvoiced_time = 0
        return amount

    def __str__(self):
        return '<{self.name} Subscription {self.id}: Subscriber id: {self.subscriber_id} \
Active: {self.is_active} Uninvoiced Time: {self.uninvoiced_time}>'.format(self=self)


class SubscriptionService:

    subscription_cls = Subscription

    def __init__(self, subscription_name, unit_cost):
        self.name = subscription_name
        self.subscribers = {}
        self.unit_cost = unit_cost
    
    def subscribe(self, subscriber_id):
        if subscriber_id not in self.subscribers:
            self.subscribers[subscriber_id] = Subscription(self.name, subscriber_id,
                                                       self.unit_cost)
        subscription = self.subscribers[subscriber_id]
        subscription.activate()
    
    def _ensure_subscriber(self, subscriber_id):
        if subscriber_id not in self.subscribers:
            raise Exception('subscriber %s is has not subscription record' % subscriber_id)
    
    def unsubscribe(self, subscriber_id):
        self._ensure_subscriber(subscriber_id)
        subscription = self.subscribers[subscriber_id]
        subscription.deactivate()
    
    def invoice(self, subscriber_id):
        self._ensure_subscriber(subscriber_id)
        subscription = self.subscribers[subscriber_id]
        amount = subscription.invoice(self.unit_cost)
        return amount
    
    def __str__(self):
        subscribers = '\n    '.join(
            '%s' % v for v in self.subscribers.values())
        return """
<{self.name} Subscription Service: Unit Cost: {self.unit_cost} Subscribers: 
    {subscribers}>""".format(self=self, subscribers=subscribers)


if __name__ == '__main__':
    service = SubscriptionService('Speed Technology', 1)
    service.subscribe(1)
    print(service)
    time.sleep(1)
    service.unsubscribe(1)
    print(service)
    amount = service.invoice(1)
    service.subscribe(2)
    time.sleep(1)
    service.unsubscribe(2)
    service.subscribe(1)
    print(service)
    