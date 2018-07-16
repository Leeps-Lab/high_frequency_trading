import sys
import os
import logging
from event import Event
from time import time, sleep
from datetime import datetime
import json

now = datetime.now().strftime('%Y-%m-%d %H-%M')
file = os.path.join(os.getcwd(),'logs/exos/' + now + '.txt')

logging.basicConfig(level=logging.INFO,
        format='%(asctime)s %(name)-6s %(levelname)s: %(message)s',
        datefmt='%m-%d %H:%M:%S',
        filename=file,
        filemode='w+')

log = logging.getLogger(__name__)


class Jump(Event):

    def __init__(self, group_id, url, filename):
        super(Jump, self).__init__(group_id, url, filename)

    def read(self):
        times, prices = super(Jump, self).read()
        prices = [int(p) for p in prices]
        self.data = list(zip(times, prices))
        logging.info('Read data.')

    def run(self, *args):
        """
        Implements jump
        """
        for t, price in self.data:
            log.info('Start wait: ' + str(time()))
            log.info('Sleep %d seconds.' % t)
            sleep(t)
            log.info('End wait: ' + str(time()))
            self.ws.send(json.dumps({'price': price}))
        sleep(0.5)
        self.ws.close()


def main():
    log.info('Jump active: ' + str(time()))
    jumping = Jump(sys.argv[1], sys.argv[2], sys.argv[3])
    jumping.read()
    jumping.add_ws()
    log.info('Websocket added: ' + str(time()))
    jumping.ws.run_forever()


if __name__ == '__main__':
    main()
