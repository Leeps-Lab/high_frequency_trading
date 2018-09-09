
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
 
    maker_role = '{self.speed}_{self.position}'
    sniper_role = '{self.speed}_sniper'

    def __init__(self, player_id):
        super().__init__(player_id)
        self.roles = {role_name: Role(role_name) for role_name in self.__class__.roles}
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
        self.duration = 0
        log.info(self.players)
    
    def process(self):
        for row in self.events:
            typ = row['type']
            func_name = self.__class__.dispatch.get(typ)
            if func_name:
                func = getattr(self, func_name)
                func(row)

    def inside_maker(self):     
        makers = [p for p in self.players.values() if p.current_role == 'maker']
        if not makers:
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
        self.duration += delta
        self.active = False

    def on(self, timestamp):
        self.start = timestamp
        self.active = True
    
    def make_profit(self, amount):
        self.profit += amount
    
    def __repr__(self):
        out = '< Role {self.name}:{self.profit}:{self.duration:.2f}>'.format(self=self)
        return out

class AggregateOutcome:

    field_name = ''
    role_map = {
        'slow_inside': ['slow_inside', 'slow_maker'],
        'slow_outside': ['slow_outside', 'slow_maker'],
        'slow_sniper': ['slow_sniper'],
        'fast_sniper': ['fast_sniper'],
        'fast_inside': ['fast_inside', 'fast_maker'],
        'fast_outside': ['fast_outside', 'fast_maker']
    }
    role_groups = {
        'base': role_map.keys(),
        'four_roles': ['slow_maker', 'slow_sniper', 'fast_maker', 'fast_sniper'],
        'fast_roles': ['fast_inside', 'fast_outside', 'fast_sniper']
    }

    def __init__(self, market):
        self.market = market
        self.role_totals = {}
        self.grouped_role_totals = {}
        self.sum_attr_per_role()
        self.group_roles()
        
    def sum_attr_per_role(self):
        cls = self.__class__
        for k, v in cls.role_map.items():
            for role_name in v:
                current = self.role_totals.get(role_name, 0)
                current += self.sum(k)
                self.role_totals[role_name] = current 

    def sum(self, role_name):
        cls = self.__class__
        total = 0
        for player in self.market.players.values():
            role = player.roles[role_name]
            amount = getattr(role, cls.field_name, None)
            if amount is None:
                log.debug('{} attr {} returned none'.format(role.name, cls.field_name))
                amount = 0
            total += amount
        return total    
    
    def group_roles(self):
        cls = self.__class__
        for group_name, role_group in cls.role_groups.items():
            group_sums = {role_name: self.role_totals[role_name] for role_name in role_group}
            self.grouped_role_totals[group_name] = group_sums


class Profit(AggregateOutcome):
    field_name = 'profit'

    def __init__(self, market):
        super().__init__(market)

class Duration(AggregateOutcome):
    field_name = 'duration'

    def __init__(self, market):
        super().__init__(market)
        self.session_length = market.duration * len(market.players)
        self.append_inactive_time(self.get_inactive_time())
    
    def get_inactive_time(self):
        inactive_time = 0
        role_total_dict = self.grouped_role_totals.get('base', None)
        if role_total_dict is None:
            return inactive_time
        active_time = sum(role_total_dict.values())
        inactive_time = self.session_length - active_time
        return inactive_time
    
    def append_inactive_time(self, inactive_time):
        self.grouped_role_totals['base']['out'] = inactive_time
        self.grouped_role_totals['four_roles']['out'] = inactive_time

def normalize(raw, factor=None):
    total = sum(raw.values())
    if total == 0:
        log.debug('total is 0.')
        return raw
    out = {k: v / total for k, v in raw.items()}
    return out

def scale(sum_dict, factor, rounded=None):
    out = {}
    for k, v in sum_dict.items():
        scaled = v * factor
        if rounded is not None:
            scaled = round(scaled, rounded)
        out[k] = scaled
    return out

def total_speed_cost(market):
    total_cost = sum([player.cost for player in market.players.values()])
    return total_cost

def take_speed_cost(profit, duration, market):
    fast_dur_dict = duration.grouped_role_totals['fast_roles']
    normal_dur = normalize(fast_dur_dict)
    total_cost = total_speed_cost(market)
    for k, v in profit.role_totals.items():
        if k in profit.__class__.role_groups['fast_roles']:
            costed = v - normal_dur[k] * total_cost
            profit.role_totals[k] = costed
    return profit
    
def BCS_results(market):
    profit = Profit(market)
    duration = Duration(market)
    profit_costed = take_speed_cost(profit, duration, market)
    normal_durations = normalize(duration.grouped_role_totals['four_roles'])
    durations_to_display = scale(normal_durations, 1, rounded=2)
    per_second_factor = 1e-4 * 60 * 1e9 / market.duration 
    base_roles_profits = profit_costed.grouped_role_totals['base']
    profits_to_display = scale(base_roles_profits, per_second_factor, rounded=2)
    return (profits_to_display, durations_to_display)

def bcs_empty_results():
    base_roles = AggregateOutcome.role_groups['base']
    profit = {role: 0  for role in base_roles}
    profit['out'] = 0
    role_group = AggregateOutcome.role_groups['four_roles']
    dur = {role: 0  for role in role_group}
    dur['out'] = 1
    return (profit, dur)

class GroupResult:
    def __init__(self, results):
        for key, value in results.items():
            setattr(self, key, value)

def BCS_process(log_file, group_id):
    out = {'profit': None, 'duration': None}
    try:
        session_events = MarketEvents.init_many(log_file)
        for market in session_events:
            if market.group == str(group_id):
                m = BCSMarket(market)
                m.process()
                profit, duration = BCS_results(m)
    except Exception as e:
        log.info('processing results failed, returning empty results.')
        profit, duration = bcs_empty_results()
        log.exception(e)
    out['profit'] = GroupResult(profit)
    out['duration'] = GroupResult(duration)
    return out

            
if __name__ == '__main__':
    out = BCS_process('hft_logging/experiment_data/CDA_hcqywgt4_3_2018-09-09_19-09', 2427)
# def aggregate(market):
#     cumul_dict = {'profit': 0,'duration': 0}
#     results = {k: dict(cumul_dict) for k in BCSPlayer.roles}
#     print(market.players)
#     for player in market.players.values():
#         for role_name, role in player.roles.items():
#             for k in cumul_dict.keys():
#                 results[role_name][k] += getattr(role, k)
#     results['duration'] = getattr(market, 'duration', None) * 1e-9
#     results['num_players'] = getattr(market, 'players', None).__len__()
#     return results

# def total_profit(results):
#     cum_profit = {role_name: 0 for role_name in BCSPlayer.roles}
#     for role_name in BCSPlayer.roles:
#         cum_profit[role_name] += results[role_name]['profit'] * 1e-4
#     return cum_profit
        
# def total_speed_cost(market):
#     total_cost = sum([player.cost for player in market.players.values()])
#     return total_cost

# def normal_duration(results):
#     session_length = results['duration'] * results['num_players']
#     if not session_length:
#         return
#     all_others = 0
#     out = {role_name: 0 for role_name in BCSPlayer.roles}
#     for role_name in BCSPlayer.roles:
#         dur = results[role_name]['duration']
#         all_others += dur
#         out[role_name] = dur / session_length
#     out['out'] = (session_length - all_others)/ session_length
#     out['slow_maker'] = out['slow_inside'] + out['slow_outside']
#     out['fast_maker'] = out['fast_inside'] + out['fast_outside']
#     return out

# def break_cost_by_role(market, results):
#     total_cost = total_speed_cost(market)
#     fast_roles = ('fast_inside', 'fast_outside', 'fast_sniper')
#     total_dur = 0
#     for role in fast_roles:
#         total_dur += results[role]['duration']
#     if not total_dur:
#         total_dur = 1
#     shares = {role: results[role]['duration'] / total_dur for role in fast_roles}
#     speed_cost_breakdown = {role: shares[role] * total_cost for role in fast_roles}
#     return speed_cost_breakdown

# def take_speed_cost(profits, speed_costs):
#     for role, cost in speed_costs.items():
#         profits[role] -= cost * 1e-4
#     return profits


# def BCS_results(market):
#     results = aggregate(market)
#     speed_costs = break_cost_by_role(market, results)
#     profits = total_profit(results)
#     profits = take_speed_cost(profits, speed_costs)
#     durations = normal_duration(results)
#     return (profits, durations)
