
from .models import Constants

class SessionPayoff:
    round_factor = 1
    c = 1 / Constants.conversion_factor

    def __init__(self, player):
        self.player = player
        print('init p payoff', player.participant.payoff)
        self.session_total = float(player.participant.payoff)
        print('init session_total', self.session_total)
    
    def random_round_payoff(self):
        cls = self.__class__
        payoff= self.player.participant.vars['round_payoff']
        payoff_round = self.player.participant.vars['payoff_round']
        self.player.final_payoff = payoff * cls.c
        return (payoff_round, payoff)

    def average_payoff(self):
        total = self.session_total
        assert self.player.subsession.total_rounds
        average_payoff = total / self.player.subsession.total_rounds
        self.player.final_payoff = average_payoff
        self.player.save()
        return average_payoff

    @classmethod
    def round(cls, payoff):
        """
        use for nice prints
        """
        num_decimals  = cls.round_factor
        scaled_payoff = round(payoff, num_decimals)
        return scaled_payoff


    



