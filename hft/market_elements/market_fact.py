import time


class MarketFact:

    defaults = {}
    name = ''
    required_input_fields = ()
    input_to_attr_map = {}
    is_time_aware = False

    def __init__(self, **kwargs):
        for k, v in self.defaults.items():
            value = v
            if k in kwargs:
                value = kwargs[k]
            setattr(self, k, value)
        if self.is_time_aware is True:
            session_duration = kwargs.get('session_duration')
            self.timer = FactTimer(session_duration=session_duration)
        self.has_changed = False

    def update(self, **kwargs):
        self.has_changed = False
        for k in self.required_input_fields:
            attr_name = k
            if k in self.input_to_attr_map:
                attr_name = self.input_to_attr_map[k]
            if hasattr(self, attr_name):
                try:
                    old_value = getattr(self, attr_name)
                    new_value = kwargs[k]
                    if old_value != new_value:
                        setattr(self, attr_name, new_value)
                        self.has_changed = True
                except KeyError:
                    raise Exception('input missing key %s : input %s' % (k, kwargs))
        if self.is_time_aware:
            self.timer.step()

    def to_kwargs(self):
        kwargs = {}
        for k in self.defaults.keys():
            kwargs[k] = getattr(self, k)
        return kwargs

    def reset_timer(self):
        if self.is_time_aware:
            self.timer.reset()
        else:
            raise Exception('market fact %s is not time aware' % self.name)


class FactTimer:

    def __init__(self, session_duration=None):
        self.time_origin = time.time()
        self.time_last_step = None
        self.time_elapsed = 0
        self.time_since_previous_step = 0
        if session_duration is not None:
            self.session_duration = session_duration

    def reset(self):
        self.__init__()

    def step(self):
        now = time.time()
        if self.time_last_step:
            self.time_since_previous_step = now - self.time_last_step
        else:
            # this is the first step.
            self.time_since_previous_step = 0
        self.time_last_step = now
        self.time_elapsed = self.time_last_step - self.time_origin




