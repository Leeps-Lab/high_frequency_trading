import json
import pandas as pd
import logging

author = 'hasan ali demirci'

log = logging.getLogger(__name__)

class MarketEvents:

    def __init__(self, group, players, events):
        self.group = group
        self.players = players
        self.events = events

    @classmethod    
    def read(cls, filename):
        try:
            f = open(filename, 'r').read()
        except FileNotFoundError:
            log.warning('Lab log file not found.')
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
                groups = record['context']['groups']
                if not getattr(cls, 'session', None):
                    session = record['context']['session']
                    setattr(cls, 'session', session)
                continue
            if events.get(group) is None:
                events[group] = []
            events[group].append(record)
        out = [cls(group, players, events[group]) 
                                for group, players in groups.items()]
        return out
    
    def __len__(self):
        return len(self.events)

    def __iter__(self):
        return iter(self.events)
    
    def __repr__(self):
        out = '< MarketEvents {length} rows >'.format(length=len(self))
        return out


class MarketIndicator:

    active_roles = ('slow_inside', 'slow_outside', 'slow_sniper', 'fast_inside', 
        'fast_outside', 'fast_sniper')
    maker_roles = ('slow_inside', 'slow_outside', 'fast_inside', 
        'fast_outside')
    role_fields = ('profit', 'total_time', 'start')
    group_fields = ('time', 'group', 'fundamental_price')
    player_fields = ('current', 'cumulative')
    current_fields = ('role', 'profit', 'speed', 'speed_cost', 'order_1', 'order_2', 'spread')

    def __init__(self, market_events):
        cls = self.__class__
        first_state = dict()
        for field in cls.group_fields:
            value = getattr(market_events, field, 0)
            first_state[field] = value
        main_fields = {key: 0 for key in cls.player_fields}
        current_fields = {key: 0 for key in cls.current_fields}
        role_fields = {key: 0 for key in cls.role_fields}
        cumulative_fields = {key: role_fields for key in cls.active_roles}
        for player in market_events.players:
            p = str(player)
            first_state[p] = main_fields
            first_state[p]['current'] = current_fields
            first_state[p]['cumulative'] = cumulative_fields
        first_state['session'] = market_events.__class__.session
        self.state = first_state
        self.events = market_events

    def find_inside_maker(self, state):
        cls = self.__class__
        spreads = {}
        for player in self.events.players:
            if player['current']['role'] not in cls.maker_roles:
                continue
            p = str(player)
            spread = state[p]['current']['spread']
            spreads.update({p:spread})
        inside_maker = min(spreads, key=spreads.get)
        return inside_maker
        
    def handle_spread(self, state, msg):
        ctx = msg['context']
        player = ctx['player_id']
        spread = ctx['spread']
        state[player]['current']['spread'] = spread
        player_is_inside = False
        inside_maker = self.find_inside_maker(state)
        if inside_maker == player:
            player_is_inside = True
        return state

    def _switch_in_n_out(self, player_in, timestamp):
        cls = self.__class__
        for player in self.events.players:
            if player == player_in:
                self.set_maker(player_in, inside=True)            
            else:
                if state[player]['role'] in cls.maker_roles:
                    self.set_maker(player)
    
    def set_maker(self, msg, player, timestamp, inside=False):
        speed = self.state[player]['current']['speed']
        side = 'inside' if inside else 'outside'
        new_role = speed + '_' + self.state
        old_role = state[player]['current']['role']
        cum = state[player]['cumulative'][old_role]

    def role_switch(self, player, old_role, new_role, timestamp):
        cls = self.__class__
        old = self.state[player]['cumulative'][old_role]
        start_time = old['start']
        if old in cls.active_roles:
            pass
    
    def role_off(self, role_dict, timestamp):
        start = role_dict['start']
        if start != 0:
            delta = timestamp - start
            start = 0
        role_dict['total_time'] += delta
        role_dict['start'] = start
        return role_dict
    
    def role_on(self, role_dict, timestamp):



        



            



if __name__ == '__main__':
    events = MarketEvents.init_many('logs/exos/2018-08-23_19-16.txt')
    print(events)
    for market in events:
        MarketIndicator(market)



# def update_choice(event, choice_type, choice_state):
#     new_state = dict(choice_state[-1])
#     player = str(event['context']['player_id'])
#     new_choice = event['context'][choice_type]
#     new_state[player] = new_choice
#     logtime = event['time']
#     new_state['time'] = logtime
#     choice_state.append(new_state)
#     return choice_state


# class MarketState:

#     start_state = {
#         'state': 'OUT',
#         'speed': False,
#         'profit': 0
#     }

#     processors = {
#         'state': update_choice,
#         'speed': update_choice,
#         'profit': None  # TODO
#     }

#     def __init__(self, market_events, player_count):
#         self.events = market_events
#         self.pc = player_count
#         self.init_states()

#     def init_states(self):
#         self.state = {k: self._default(v) for k, v in self.start_state.items()}

#     def _default(self, initial):
#         first_row = {str(i + 1): initial for i in range(self.pc)}
#         first_row.update({'time': time_start})
#         return [first_row]

#     def process(self):
#         for event in self.events:
#             typ = event['type']
#             try:
#                 current_state = self.state[typ]
#                 new_state = self.processors[typ](event, typ, current_state)
#             except KeyError:
#                 log.info('Processor not available for the type.')
#                 continue
#             self.state[typ] = new_state

#     def dump(self):
#         return {self.events.group_id : self.state}
    
#     def export_json(self, filename):
#         out = self.dump()
#         with open(filename, 'w') as f:
#             json.dump(out, f)



# def test():
#     market = MarketEvents('./logs/exp_20180522 14.04.txt', group_id)
#     state = MarketState(market, player_count)
#     state.process()
#     state.export_json('test.json')


# if __name__ == '__main__':
#     test()
# © 2018 GitHub, Inc.
# Terms
# Privacy
# Security
# Status
# Help
# Contact GitHub
# Pricing
# API
# Training
# Blog
# About
# Press h to open a hovercard with more details.