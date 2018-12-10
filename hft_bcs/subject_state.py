class BaseSubjectState:

    __slots__ = ()

    def __init__(self, **kwargs):
        for slot in self.__slots__:
            setattr(self, slot, kwargs.get(slot, None))

    @classmethod
    def from_trader(cls, trader):
        kwargs = {slot: getattr(trader, slot, None) for slot in cls.__slots__}
        return cls(**kwargs)


class BCSSubjectState(BaseSubjectState):

    __slots__ = ('orderstore', 'exchange_host', 'exchange_port', 'group_id', 'id_in_group', 
        'id', 'code', 'role', 'fp', 'speed_on',  'speed_unit_cost', 'spread', 'speed_on_start_time', 
        'endowment', 'cost', 'time_on_speed', 'last_message_time')

class BCSInvestorState(BaseSubjectState):
    __slots__ = ('orderstore', 'exchange_host', 'exchange_port', 'group_id')


