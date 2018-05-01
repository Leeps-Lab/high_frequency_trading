import sys
import logging
from event import Event
from utility import Get_Time
from time import sleep
import json

file = 'jump-log.txt'

logging.basicConfig(level=logging.INFO,
        format='%(asctime)s %(name)-6s %(levelname)s: %(message)s',
        datefmt='%m-%d %H:%M:%S',
        filename=file,
        filemode='w')

logging.getLogger(__name__)


class Jump(Event):

    def __init__(self, group_id, url, filename):
        super(Jump, self).__init__(group_id, url, filename)

    def read(self):
        times = super().read()
        self.data = list(times.values)
        logging.info('Read data.')

    def run(self, *args):
        """
        Implements jump
        """
        for t, price in self.data:
            logging.info('Start wait: ' + str(Get_Time()))
            logging.info('Sleep %d seconds.' % t)
            sleep(t)
            logging.info('End wait: ' + str(Get_Time()))
            self.ws.send(json.dumps({'price': price}))
        sleep(0.5)
        self.ws.close()


def main():
    logging.info('Jump active: ' + str(Get_Time()))
    jumping = Jump(sys.argv[1], sys.argv[2], sys.argv[3])
    jumping.read()
    jumping.add_ws()
    logging.info('Websocket added: ' + str(Get_Time()))
    jumping.ws.run_forever()


if __name__ == '__main__':
    main()
