import websocket
try:
    import thread
except ImportError:
    import _thread as thread
import sys
import pandas as pd
import logging
import json
from time import sleep
import datetime


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
        arrive_times = pd.read_csv(self.filename)
        first_arv = int(arrive_times.loc[0, 'time'])
        arrive_times['time'] = arrive_times['time'].diff()
        arrive_times.loc[0, 'time'] = first_arv
        return arrive_times

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

