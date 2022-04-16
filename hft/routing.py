from channels.routing import route_class
from .consumers import SubjectConsumer, ExogenousEventConsumer
from otree.channels.routing import channel_routing

channel_routing += [
    route_class(SubjectConsumer, path=r"^/hft/(?P<subsession_id>\w+)/(?P<group_id>\w+)/(?P<player_id>\w+)/"),
    route_class(ExogenousEventConsumer, path=r"^/hft_exogenous_event/(?P<subsession_id>\w+)"),
]
 