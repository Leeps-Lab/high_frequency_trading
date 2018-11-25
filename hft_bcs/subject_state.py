class BaseSubjectState:

    __slots__ = ()

    def __init__(self, **kwargs):
        for slot in self.__slots__:
            setattr(self, slot, kwargs.get(slot, None))

    def from_trader(self, trader):
        for slot in self.__slots__:
            setattr(self, slot, getattr(trader, slot, None))


class BCSSubjectState(BaseSubjectState):

    __slots__ = ('group_id', 'id_in_group', 'id', 'code', 'role', 'fp', 
        'speed_on',  'speed_unit_cost', 'spread', 'speed_on_start_time', 
        'endowment', 'cost', 'time_on_speed', 'last_message_time')


