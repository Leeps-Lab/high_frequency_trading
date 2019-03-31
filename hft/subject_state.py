from .orderstore import OrderStore


class SubjectStateFactory:
    @staticmethod
    def get_state(session_format):
        if session_format == 'BCS':
            return BCSSubjectState
        elif session_format == 'elo':
            return ELOSubjectState
        else:
            raise Exception('invalid session format: %s' % session_format)

class BaseSubjectState:

    orderstore_cls = None
    __slots__ = ()

    def __init__(self, **kwargs):
        for slot in self.__slots__:
            setattr(self, slot, kwargs.get(slot, None))

    @classmethod   
    def from_otree_player(cls, player):
        kwargs = {slot: getattr(player, slot, None) for slot in cls.__slots__}
        orderstore = cls.orderstore_cls(player.id, player.id_in_group)
        kwargs['orderstore'] = orderstore
        return cls(**kwargs)

    @classmethod
    def from_trader(cls, trader):
        kwargs = {slot: getattr(trader, slot, None) for slot in cls.__slots__}
        return cls(**kwargs)


class BCSSubjectState(BaseSubjectState):
    orderstore_cls = OrderStore
    __slots__ = ('orderstore', 'exchange_host', 'exchange_port', 'group_id', 'id_in_group', 
        'id', 'code', 'role', 'fp', 'speed_on',  'speed_unit_cost', 'spread', 'speed_on_start_time', 
        'endowment', 'cost', 'time_on_speed', 'last_message_time', 'market')

class ELOSubjectState(BaseSubjectState):
    orderstore_cls = OrderStore
    __slots__ = ('orderstore', 'exchange_host', 'exchange_port', 'group_id', 'id_in_group', 
        'id', 'code', 'role', 'speed_on',  'technology_unit_cost', 'spread', 'speed_on_start_time', 
        'wealth', 'cash', 'reference_price', 'cost', 'time_on_speed', 'last_message_time', 
        'market_id', 'sliders', 'best_bid', 'best_offer', 'target_bid', 'target_offer', 
        'order_imbalance', 'implied_bid', 'implied_offer', 'volume_at_best_offer', 
        'volume_at_best_bid', 'wait_for_best_bid', 'wait_for_best_offer', 'technology_cost',
        'next_bid', 'next_offer', 'tax')    

class LEEPSInvestorState(BaseSubjectState):
    orderstore_cls = OrderStore
    __slots__ = ('orderstore', 'exchange_host', 'exchange_port', 'market_id', 'endowment',
        'inventory', 'id')
    

