# from hft_bcs.utility import nanoseconds_since_midnight
import json
import pytz
from collections import deque
from itertools import count
from hft_bcs.utility import nanoseconds_since_midnight

author = 'hasan ali demirci'


class ExperimentLogger:

    def __init__(self):
        self.logs = deque()
        self.log_file = None
    
    def __call__(self, log_file):
        self.logs = deque()
        self.log_file = log_file
    
    def log(self, log):
        self.logs.append(log)
    
    def dump(self):
        with open(self.log_file,'a') as f:
            for i in count():
                try:
                    log = self.logs.popleft()
                except IndexError:
                    return
                json_log = log.jsonify()
                f.write(json_log)


class ExperimentLog:
    base_fields = ('time', 'group_id', 'level', 'event_type')
    event_type = None
    level = None
    context_fields = ()
    model_fields = ()
    context_key = 'context'
    model_key = 'model'
    time_key = 'time'

    def __init__(self, **kwargs):
        model = kwargs.pop(self.model_key)
        for field in self.model_fields:
            att = getattr(model, field)
            setattr(self, field, att)
        for k, v in kwargs.items():
            setattr(self, k, v)
        setattr(self, self.time_key, nanoseconds_since_midnight())

    def jsonify(self):
        out = {self.context_key: {}}
        for field in self.base_fields:
            out[field] = getattr(self, field)
        for field in self.context_fields:
            out[self.context_key][field] = getattr(self, field)
        json_out = json.dumps(out)
        return json_out

class ProfitLog(ExperimentLog):
    event_type = 'profit'
    level = 'market'
    context_fields = ('id', 'profit', 'endowment')
    model_fields = ('id', 'group_id', 'endowment')

class CostLog(ExperimentLog):
    event_type = 'cost'
    level = 'market'
    context_fields = ('id', 'cost')
    model_fields = ('id', 'group_id', 'cost')

class EnterOrderLog(ExperimentLog):
    event_type = 'enter'
    level = 'exch'
    context_fields = ('id', 'token', 'timestamp', 'side', 'time_in_force', 'price')
    model_fields = ('token', 'timestamp', 'side', 'time_in_force', 'price')

class ExecuteOrderLog(ExperimentLog):
    event_type = 'exec'
    level = 'exch'
    context_fields = ('id', 'token', 'timestamp', 'price')
    model_fields = ('token', 'timestamp', 'price')

class ReplaceOrderLog(ExperimentLog):
    event_type = 'replace'
    level = 'exch'
    context_fields = ('id', 'replaced_token', 'timestamp', 'new_token')
    model_fields = ('group_id', 'id')  

class CancelOrderLog(ExperimentLog):
    event_type = 'cancel'
    level = 'exch'
    context_fields = ('id', 'token', 'timestamp')
    model_fields = ('token', 'timestamp')  

class SpreadLog(ExperimentLog):
    event_type = 'spread'
    level = 'choice'
    context_fields = ('id', 'spread')
    model_fields = ('id', 'group_id', 'spread')

class RoleLog(ExperimentLog):
    event_type = 'role'
    level = 'choice'
    context_fields = ('id', 'role')
    model_fields = ('id', 'group_id', 'role')

class SpeedLog(ExperimentLog):
    event_type = 'speed'
    level = 'choice'
    context_fields = ('id', 'speed')
    model_fields = ('id', 'group_id', 'speed')   

class JumpLog(ExperimentLog):
    event_type = 'jump'
    level = 'market'
    context_fields = ('jump')
    model_fields = ('id', 'group_id')    

class InvestorLog(ExperimentLog):
    event_type = 'investor'
    level = 'market'
    context_fields = ('side')
    model_fields = ('id', 'group_id') 

class StartLog(ExperimentLog):
    event_type = 'start'
    level = 'exch'
    context_fields = ()
    model_fields = ('id', 'is_trading') 

class EndLog(ExperimentLog):
    event_type = 'end'
    level = 'exch'
    context_fields = ()
    model_fields = ('id', 'is_trading')

class HeaderLog(ExperimentLog):
    event_type = 'header'
    level = 'header'
    context_fields = ('side')
    model_fields = ('code', 'design', 'batch_length', 'round_length', 'round_number')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.group_id = 0 

class   MockPlayer:
    def __init__(self):
        self.id = 8
        self.group_id = 2
        self.profit = 24
        self.endowment = 22


experiment_logger = ExperimentLogger()

if __name__ == '__main__':
    mock_player = MockPlayer()
    test_dict = {
        'model': mock_player, 'profit': 15, 'time': 10,
    }
    logger = ExperimentLogger()
    logger('testing.txt')
    logger.log(ProfitLog(**test_dict))
    logger.dump()





            
