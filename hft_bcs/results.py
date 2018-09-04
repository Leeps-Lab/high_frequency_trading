
import json
import logging

author = 'hasan ali demirci'

log = logging.getLogger(__name__)

class MarketEvents:

    def __init__(self, group, players, events, **kwargs):
        self.group = group
        self.players = players
        self.events = events
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod    
    def read(cls, filename):
        f = open(filename, 'r').read()
        # -1 since we split by a new line
        out = f.split('\n')[:-1]
        return out

    @classmethod    
    def init_many(cls, filename):
        json_rows = cls.read(filename)
        events = {}
        for row in json_rows:   
            record = json.loads(row)
            group = str(record['group'])
            if group == '0':  # row is header
                groups = record['context'].pop('groups')
                if not getattr(cls, 'session', None):
                    session = record['context'].pop('session')
                    setattr(cls, 'session', session)
                instance_vars = record['context']
                continue
            if events.get(group) is None:
                events[group] = []
            events[group].append(record)
        out = [cls(group, players, events[group], **instance_vars) 
                                for group, players in groups.items()]
        return out

    def __len__(self):
        return len(self.events)

    def __iter__(self):
        return iter(self.events)
    
    def __repr__(self):
        out = '< MarketEvents {length} rows >'.format(length=len(self))
        return out


class Player:

    roles = ()

    def __init__(self, player_id):
        self.id = player_id
        self.roles = {}
        self.current_role = None
        self.profit = 0
        self.cost = 0

    def raw_make_profit(self, amount):
        self.profit += amount
        self.make_profit(amount)
    
    def make_profit(self, amount):
        raise NotImplementedError()

    def take_cost(self, amount):
        self.cost += amount
    
    def active_role(self):
        active_role = [role for role in self.roles.values() if role.active]
        assert len(active_role) <= 1
        if active_role:
            return active_role.pop()
    
    def turn_off(self, timestamp):
        for role_name in self.__class__.roles:
            self.roles[role_name].off(timestamp)

        

class BCSPlayer(Player):

    roles = ('slow_inside', 'slow_outside', 'slow_sniper', 'fast_inside', 
        'fast_outside', 'fast_sniper')
    role_groups = ('three_role_group')
    three_role_group = {
        'slow_maker': ('slow_inside', 'slow_outside'),
        'fast_maker': ('fast_inside', 'fast_outside'),
        'slow_sniper': ('slow_sniper',),
        'fast_sniper': ('fast_sniper',),
        }
 
    maker_role = '{self.speed}_{self.position}'
    sniper_role = '{self.speed}_sniper'

    def __init__(self, player_id):
        super().__init__(player_id)
        cls = self.__class__
        self.roles = {role_name: Role(role_name) for role_name in cls.roles}
        self.speed = 'slow'
        self.spread = None
        self.position = 'outside'
        self.current_role = 'out'
    
    def make_profit(self, amount):
        active_role = self.active_role()
        if active_role:
            active_role.make_profit(amount)
            self.roles[active_role.name] = active_role

    def adjust_maker(self, timestamp, position):
        active_role = self.active_role()
        active_role.off(timestamp)
        self.position = position
        new_role_name = self.__class__.maker_role.format(self=self)
        new_role = self.roles.pop(new_role_name)
        new_role.on(timestamp)
        self.roles[active_role.name] = active_role
        self.roles[new_role.name] = new_role
    
    def role_change(self, new_role, time):
        active_role = self.active_role()
        if active_role:
            active_role.off(time)
            self.roles[active_role.name] = active_role
        sub_role_name = self.find_next_role(new_role)
        if sub_role_name:
            self.roles[sub_role_name].on(time)

    def find_next_role(self, new_role):
        cls = self.__class__
        key = None
        if new_role == 'sniper':
            key = cls.sniper_role.format(self=self)
        elif new_role == 'maker':
            key = cls.maker_role.format(self=self)
        else:
            pass
        return key

    def speed_change(self, new_speed, time):
        self.speed = new_speed
        active_role = self.active_role()
        if active_role:
            active_role.off(time)
            self.roles[active_role.name] = active_role
        if self.current_role != 'out':
            if self.current_role == 'sniper':
                sub_role_name = self.__class__.sniper_role.format(self=self)
            elif self.current_role == 'maker':
                sub_role_name = self.__class__.maker_role.format(self=self)
        self.roles[sub_role_name].on(time)

    def __repr__(self):
        out = '< BCSPlayer {self.id}:{self.current_role}:{self.spread}>'.format(self=self)
        return out

class BCSMarket:

    active_roles = ('maker', 'sniper')
    dispatch = {
        'profit': 'handle_profit',
        'speed': 'handle_speed',
        'spread': 'handle_spread',
        'state': 'handle_role_change',
        'start': 'handle_start',
        'cost': 'handle_cost',
        'end': 'handle_end'
    }

    def __init__(self, events):
        self.players = {p: BCSPlayer(p) for p in events.players}
        self.events = events
        log.info(self.players)
    
    def process(self):
        for row in self.events:
            typ = row['type']
            func_name = self.__class__.dispatch.get(typ)
            if func_name:
                func = getattr(self, func_name)
                func(row)

    def inside_maker(self):     
        print(self.players.values())   
        makers = [p for p in self.players.values() if p.current_role == 'maker']
        print(makers)
        if makers is None:
            return
        fun = (lambda x: x.spread if x.spread is not None else self.events.spread)
        makers.sort(key=fun, reverse=True)
        inside_maker = makers.pop()
        return inside_maker

    def handle_spread(self, msg):
        player_id = msg['context']['player_id']
        spread = msg['context']['spread']
        time = msg['time']
        self.players[player_id].spread = spread
        self.arrange_makers(time)
    
    def handle_start(self, msg):
        time = msg['time']
        self.start = time
    
    def handle_end(self, msg):
        time = msg['time']
        self.duration = time - self.start
        for player in self.players.values():
            player.turn_off(time)

    def handle_role_change(self, msg):
        player_id = msg['context']['player_id']
        new_role = msg['context']['state'].lower()
        time = msg['time']
        old_role = str(self.players[player_id].current_role)
        self.players[player_id].current_role = new_role
        self.players[player_id].role_change(new_role, time)
        if old_role == 'maker' or new_role == 'maker':
            self.arrange_makers(time)

    def handle_profit(self, msg):
        player_id = msg['context']['player_id']
        profit = msg['context']['profit']
        self.players[player_id].raw_make_profit(profit)

    def handle_cost(self, msg):
        player_id = msg['context']['player_id']
        cost = msg['context']['cost']  
        self.players[player_id].take_cost(cost)     

    def handle_speed(self, msg):
        time = msg['time']
        player_id = msg['context']['player_id']
        speed = msg['context']['speed']
        new_speed = 'fast' if speed else 'slow'
        self.players[player_id].speed_change(new_speed, time)

    def arrange_makers(self, time):
        inside_maker = self.inside_maker()
        if not inside_maker:
            return
        players = self.players
        for k, p in players.items():
            if p.current_role == 'maker' and p != inside_maker:
                p.adjust_maker(time, 'outside')
            elif p is inside_maker:
                p.adjust_maker(time, 'inside')
            self.players[k] = p

      
class Role:

    def __init__(self, name):
        self.active = False
        self.name = name
        self.start = None
        self.profit = 0
        self.duration = 0
        self.history = []
    
    def off(self, timestamp):
        if not self.active:
             log.debug('%s role is already off.' % self.name)
             return
        delta = timestamp - self.start
        self.duration += delta * 1e-9
        self.active = False

    def on(self, timestamp):
        self.start = timestamp
        self.active = True
    
    def make_profit(self, amount):
        self.profit += amount
    
    def __repr__(self):
        out = '< Role {self.name}:{self.profit}:{self.duration:.2f}>'.format(self=self)
        return out

                    
def aggregate(market):
    cumul_dict = {'profit': 0,'duration': 0}
    results = {k: dict(cumul_dict) for k in BCSPlayer.roles}
    print(market.players)
    for player in market.players.values():
        for role_name, role in player.roles.items():
            for k in cumul_dict.keys():
                results[role_name][k] += getattr(role, k)
    results['duration'] = getattr(market, 'duration', None) * 1e-9
    results['num_players'] = getattr(market, 'players', None).__len__()
    return results

def total_profit(results):
    cum_profit = {role_name: 0 for role_name in BCSPlayer.roles}
    for role_name in BCSPlayer.roles:
        cum_profit[role_name] += results[role_name]['profit'] * 1e-4
    return cum_profit
        
def total_speed_cost(market):
    total_cost = sum([player.cost for player in market.players.values()])
    return total_cost

def normal_duration(results):
    session_length = results['duration'] * results['num_players']
    all_others = 0
    out = {role_name: 0 for role_name in BCSPlayer.roles}
    for role_name in BCSPlayer.roles:
        dur = results[role_name]['duration']
        all_others += dur
        out[role_name] = dur / session_length
    out['out'] = (session_length - all_others)/ session_length
    out['slow_maker'] = out['slow_inside'] + out['slow_outside']
    out['fast_maker'] = out['fast_inside'] + out['fast_outside']
    return out

def break_cost_by_role(market, results):
    total_cost = total_speed_cost(market)
    fast_roles = ('fast_inside', 'fast_outside', 'fast_sniper')
    total_dur = 0
    for role in fast_roles:
        total_dur += results[role]['duration']
    if not total_dur:
        total_dur = 1
    shares = {role: results[role]['duration'] / total_dur for role in fast_roles}
    speed_cost_breakdown = {role: shares[role] * total_cost for role in fast_roles}
    return speed_cost_breakdown

def take_speed_cost(profits, speed_costs):
    for role, cost in speed_costs.items():
        profits[role] -= cost * 1e-4
    return profits


def BCS_results(market):
    results = aggregate(market)
    speed_costs = break_cost_by_role(market, results)
    profits = total_profit(results)
    profits = take_speed_cost(profits, speed_costs)
    durations = normal_duration(results)
    return (profits, durations)


if __name__ == '__main__':
    events = MarketEvents.init_many('hft_logging/experiment/CDA_nlwehpop_3_2018-09-02_20-18')
    results = [BCSMarket(market) for market in events]
    for market in results:
        market.process()
        p, d = BCS_results(market)