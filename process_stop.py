from websocket import create_connection
ws = create_connection("ws://127.0.0.1:8000/hft/stop_exg")
ws.send('kill investors and jumps..')