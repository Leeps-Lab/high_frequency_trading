from collections import abc

class MarketRoleGroup:

    def __init__(self, *args):
        self.role_names = []
        for name in args:
            setattr(self, name, TrackedMarketRole(name))
            self.role_names.append(name)

    def update(self, timestamp, player_id, new_role_name):
        int_player_id = int(player_id)
        new_role = getattr(self, new_role_name, None) 
        if not isinstance(new_role, TrackedMarketRole):
            raise ValueError('invalid role names for %s, new_role: %s' % (
                self, new_role))
        for name in self.role_names:
            role = getattr(self, name)
            if int_player_id in role:
                role.remove(timestamp, int_player_id)
                break
        new_role.add(timestamp, int_player_id)

    def __getitem__(self, role_names):
        player_ids = []
        if isinstance(role_names, abc.Sequence):
            for name in role_names:
                role_property = getattr(self, name)
                if role_property:
                    player_ids.extend(role_property.get_player_ids())
        else:
            role_property = getattr(self, name)
            if role_property:
                player_ids.extend(role_property.get_player_ids())
        return player_ids
    
    def __str__(self):
        roles = ' '.join(str(getattr(self, role_name)) for role_name in self.role_names)
        out = 'Market Roles: {roles}'.format(roles=roles)
        return out

class TrackedMarketRole:

    def __init__(self, role_id):
        self.role_id = role_id
        self.players = {}
        self.time_spent_per_player = {}
    
    def add(self, timestamp , player_id):
        self.players[player_id] = timestamp
        if player_id not in self.time_spent_per_player:
            self.time_spent_per_player[player_id] = 0
    
    def remove(self, timestamp, player_id):
        try:
            start_time = self.players[player_id]
        except:
            raise Exception('player %s is not in role: %s' % (
                player_id, self))
        else:
            time_spent = timestamp - start_time
            self.time_spent_per_player[player_id] += time_spent
        del self.players[player_id]

    
    def __str__(self):
        return '%s: %s' % (self.role_id, ' '.join(str(k) for k in self.players.keys()))
    
    def __contains__(self, player_id):
        return player_id in self.players.keys()

    def get_player_ids(self):
        return self.players.keys()
    