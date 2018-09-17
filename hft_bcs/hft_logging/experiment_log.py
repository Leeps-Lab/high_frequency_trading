# from hft_bcs.utility import nanoseconds_since_midnight
import json
import datetime
import pytz
"""
this will replace current experiment data logging
"""
author = 'hasan ali demirci'

class ExperimentLog:
    base_fields = ('time', 'group_id', 'level', 'type')
    context_fields = ()
    model_fields = ()
    status_fields = ()
    context_key = 'context'
    model_key = 'model'
    status_func = 'status'
    time_key = 'time'

    def __init__(self, **kwargs):
        cls = self.__class__
        model = kwargs.pop(cls.model_key)
        for field in cls.model_fields:
            att = getattr(model, field)
            setattr(self, field, att)
        for field in cls.status_fields:
            get_status = getattr(model, cls.status_func)
            att = get_status(field=field)
            setattr(self, field, att)
        for k, v in kwargs.items():
            setattr(self, k, v)
        time = nanoseconds_since_midnight()
        setattr(self, cls.time_key, time)

    def dump(self):
        cls = self.__class__
        out = {cls.context_key: {}}
        for field in cls.base_fields:
            out[field] = getattr(self, field)
        for field in cls.context_fields:
            out[cls.context_key][field] = getattr(self, field)
        json_out = json.dumps(out)
        return json_out

    #         group=self.group_id, level='market', typ='profit',
    #         source='cross', pid=self.id, stamp=timestamp,
    #         endowment=self.status(field='profit'), profit=pi
    # time = nanoseconds_since_midnight()
    # level, typ = kwargs.pop('level'), kwargs.pop('typ')
    # group = kwargs.pop('group')
    # result = {
    #     'time': time,
    #     'group': group,
    #     'level': level,
    #     'type': typ,
    #     'context': dispatch[typ](**kwargs)
    # }

    #     result = {
    #     'player_id': pid, 'profit': profit, 'source': source, 
    #     'timestamp': stamp, 'endowment': endowment
    # }

class ProfitLog(ExperimentLog):
    context_fields = ('id', 'profit')
    model_fields = ('id', 'group_id')
    status_fields = ('profit',)

class Player:
    def __init__(self):
        self.id = 8
        self.group_id = 2
        self.profit = 24

    def status(self, field=None):
        return getattr(self, field)

if __name__ == '__main__':
    mock_player = Player()
    test_dict = {
        'model': mock_player, 'profit': 15, 'type': 'profit', 'level': 'kol', 'time': 10
    }
    log = ProfitLog(**test_dict)
    test_json = ProfitLog(**test_dict).dump()
    print(test_json)




            
