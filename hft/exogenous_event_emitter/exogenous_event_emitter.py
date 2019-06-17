import websocket
try:
    import thread
except ImportError:
    import _thread as thread
import logging
import sys
import time
import json

log = logging.getLogger(__name__)

class ExogenousEventClient(object):

    def __init__(self, url, event_type, data):
        self.url = url
        self.data = json.loads(data)
        self.event_type = event_type

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

        ws = websocket.WebSocketApp(self.url + '/',
                    on_message = on_message,
                    on_error = on_error,
                    on_close = on_close)

        ws.on_open = on_open
        self.ws = ws

class ExogenousEventEmitter(ExogenousEventClient):

    def run(self):
        """
        Implements investor behaviour
        """
        orders = self.data
        time_prev = 0
        for row in orders:
            payload = row['fields']
            msg_time = payload['arrival_time']
            sleep_time = msg_time - time_prev
            payload['type'] = self.event_type
            log.info('Sleep %f (%f:%f) seconds.' % (sleep_time, time_prev, msg_time))
            time.sleep(sleep_time)
            self.ws.send(json.dumps(payload))
            time_prev = msg_time
        time.sleep(0.5)
        self.ws.close()

def main():
    investor = ExogenousEventEmitter(*sys.argv[1:])
    investor.add_ws()
    investor.ws.run_forever()


if __name__ == '__main__':
    main()

