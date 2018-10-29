import websocket
try:
    import thread
except ImportError:
    import _thread as thread
import sys
import numpy as np
import logging
import json
import datetime
import csv
from collections import deque
import sys
import os
import time
from datetime import datetime
import json

log = logging.getLogger(__name__)


class ExogenousEvent(object):

    def __init__(self, group_id, url, filename):
        self.group_id = group_id
        self.url = url
        self.filename = filename
        self.data = deque()

    def read(self):
        """
        read arrival side&time
        store as (time, side) tuples
        """
        with open(self.filename) as f:
            reader=csv.reader(f)
            for row in reader:
                self.data.appendleft(row)

    def run(self):
        """
        override this
        """
        pass

    def add_ws(self):
        """
        Websocket to connect to the experiment
        """
        def on_message(ws, message):
            print(message)

        def on_error(ws, error):
            pass

        def on_close(ws):
            pass

        def on_open(ws):
            thread.start_new_thread(self.run, ())

        ws = websocket.WebSocketApp(self.url + self.group_id + '/',
                    on_message = on_message,
                    on_error = on_error,
                    on_close = on_close)

        ws.on_open = on_open
        self.ws = ws

class BCSExogenousEvent(ExogenousEvent):

    def __init__(self, group_id, url, filename):
        super().__init__(group_id, url, filename)
        self.read()

    def run(self):
        """
        Implements investor behaviour
        """
        column_names = self.data.pop()
        time_prev = 0
        for row in range(len(self.data)):
            row = self.data.pop()
            msg_time = float(row[0])
            sleep_time = msg_time - time_prev
            msg = {}
            for ix, field in enumerate(row):
                key = column_names[ix]
                msg[key] = field
            log.info('Sleep %f (%f:%f) seconds.' % (sleep_time, time_prev, msg_time))
            time.sleep(sleep_time)
            self.ws.send(json.dumps(msg))
            time_prev = msg_time
        time.sleep(0.5)
        self.ws.close()


def main():
    investor = BCSExogenousEvent(sys.argv[1], sys.argv[2], sys.argv[3])
    investor.read()
    investor.add_ws()
    investor.ws.run_forever()


if __name__ == '__main__':
    main()

