import websocket
try:
    import thread
except ImportError:
    import _thread as thread
import sys
import numpy as np
import logging
import json
from time import sleep
import datetime
import csv

class Event(object):

    def __init__(self, group_id, url, filename):
        self.group_id = group_id
        self.url = url
        self.filename = filename

    def read(self):
        """
        read arrival side&time
        store as (time, side) tuples
        """
        times = []
        events = []
        with open(self.filename) as f:
            reader=csv.reader(f)
            for row in reader:
                times.append(row[0])
                events.append(row[1])
        events = events[1:]
        first_arrival = int(times[1])
        times = np.asarray(times[1:], dtype = np.float)
        times = np.ediff1d(times)
        times = np.concatenate([[first_arrival], times]).tolist()
        return (times, events)

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
            print(error)

        def on_close(ws):
            print ("closed")

        def on_open(ws):
            thread.start_new_thread(self.run, ())

        ws = websocket.WebSocketApp(self.url + self.group_id + '/',
                    on_message = on_message,
                    on_error = on_error,
                    on_close = on_close)

        ws.on_open = on_open
        self.ws = ws

