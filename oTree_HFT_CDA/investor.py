import websocket

try:
    import thread
except ImportError:
    import _thread as thread
import time
import sys
import pandas as pd



class Investor(object):

    def __init__(self, group_id, filename):
        self.group_id = group_id
        self.filename = filename
        self.url = 'ws://127.0.0.1:8000/otree_HFT_CDA/investor/group'

    def read(self):
        """
        read arrival side&time
        store as (time, side) tuples
        """
        arrive_times = pd.read_csv(self.filename)
        arrive_times['time'] = arrive_times['time'].diff()
        arrive_times.loc[0, 'time'] = 0
        time_side_tuples = list(arrive_times.itertuples(index=False, name=None))
        self.data = time_side_tuples

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
            def run(*args):
                """
                Implements investor behaviour
                """
                for t, side in self.data:
                    time.sleep(t)
                    ws.send(side)
                ws.close()
            thread.start_new_thread(run, ())

        ws = websocket.WebSocketApp(self.url + self.group_id,
                                    on_message = on_message,
                                    on_error = on_error,
                                    on_close = on_close)
        ws.on_open = on_open
        self.ws = ws


def main():
    investor = Investor(sys.argv[1], sys.argv[2])
    investor.read()
    investor.add_ws()
    investor.ws.run_forever()


if __name__ == '__main__':
    main()
