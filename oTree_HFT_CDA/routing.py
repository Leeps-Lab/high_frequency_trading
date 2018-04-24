from channels.routing import route, include
from .consumers import ws_receive, ws_connect, ws_disconnect, ws_receive_inv
from otree.channels.routing import channel_routing



players_routing = [
    route("websocket.connect",
    ws_connect,  path=r'^/(?P<group_name>\w+)$'),
    route("websocket.receive",
    ws_receive,  path=r'^/(?P<group_name>\w+)$'),
    route("websocket.disconnect",
    ws_disconnect,  path=r'^/(?P<group_name>\w+)$'),
    ]

investor_routing = [
    route("websocket.connect",
    ws_connect_inv,  path=r'^/(?P<group_name>\w+)$'),
    route("websocket.receive",
    ws_receive_inv,  path=r'^/(?P<group_name>\w+)$'),
    route("websocket.disconnect",
    ws_disconnect,  path=r'^/(?P<group_name>\w+)$'),
    ]

channel_routing += [
    include(players_routing, path=r"^/otree_HFT_CDA"),
    include(investor_routing, path=r"^/otree_HFT_CDA/investor"),
]
