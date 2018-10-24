class BaseSubjectState:

    __slots__ = ()

    def __init__(self, **kwargs):
        for slot in self.__slots__:
            setattr(self, slot, kwargs.get(slot, None))

    def from_trader(self, trader):
        for slot in self.__slots__:
            setattr(self, slot, getattr(trader, slot, None))


class BCSSubjectState(BaseSubjectState):

    __slots__ = ('exchange_address', 'group_id', 'id_in_group', 'id', 'code', 'role', 'fp', 'speed', 
                'speed_unit_cost', 'spread', 'prev_speed_update', 'endowment', 'cost', 'speed_on')


