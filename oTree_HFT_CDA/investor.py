import sys
import logging
from event import Event
from time import sleep
from utility import Get_Time
import json

file = 'inv-log.txt'

logging.basicConfig(level=logging.INFO,
        format='%(asctime)s %(name)-6s %(levelname)s: %(message)s',
        datefmt='%m-%d %H:%M:%S',
        filename=file,
        filemode='w')

logging.getLogger(__name__)



class Investor(Event):

    def __init__(self, group_id, url, filename):
        super(Investor, self).__init__(group_id, url, filename)

    def read(self):
        times = super().read()        
        time_side_tuples = list(times.itertuples(index=False, name=None))
        self.data = time_side_tuples
        logging.info('Read data.')

    def run(self):
        """
        Implements investor behaviour
        """
        for t, side in self.data:
            logging.info('Start wait: ' + str(Get_Time()))
            logging.info('Sleep %d seconds.' % t)
            sleep(t)
            logging.info('End wait: ' + str(Get_Time()))
            self.ws.send(json.dumps({'side': side}))
        self.ws.close()


def main():
    logging.info('Investor active: ' + str(Get_Time()))
    investor = Investor(sys.argv[1], sys.argv[2], sys.argv[3])
    investor.read()
    investor.add_ws()
    logging.info('Websocket added: ' + str(Get_Time()))
    investor.ws.run_forever()


if __name__ == '__main__':
    main()



