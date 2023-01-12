from ._builtin import Page


def formatNicely(amount):
    return "{:.2f}".format(amount)
    # return "{:.2f}".format(amount).replace('.', ',') # for EUR


class MyPage(Page):
    #timeout_seconds = 5*60
    def vars_for_template(self):
        try:
            vft = {
                    'random_payoff': self.participant.vars['random_payoff'],
                    'random_round_num': self.participant.vars['random_round_num'],
                    'earned_more_than_max': self.participant.vars['earned_more_than_max'],
                    'participation_fee': self.participant.vars['participation_fee'],
                    'exchange_rate': self.participant.vars['exchange_rate'],
                    'total_cash_payment_before_exchange_rate': float(self.participant.vars['payment_before_participation_fee'] / self.participant.vars['exchange_rate']),
                    'negative_payoff': self.participant.vars['negative_payoff'],
                    'max_payment': self.player.participant.vars['max_payment'],
                    }
        except:
            vft = {
                    'random_payoff': False,
                    'random_round_num': 0,
                    'earned_more_than_max': False,
                    'participation_fee': self.participant.vars['payment'],
                    'exchange_rate': 0,
                    'negative_payoff': False,
                    }

        vft['feedback_next_button_timeout'] = self.session.config['feedback_next_button_timeout']
        vft['consent'] = self.player.participant.vars['consent']
        vft['overbooked'] = self.player.participant.vars['overbooked']
        vft['underbooked'] = self.player.participant.vars['underbooked']
        vft['nicePayment'] = formatNicely(self.participant.vars['payment'])

        # Set payoff
        self.player.payoff = vft['nicePayment']

        return vft

page_sequence = [
    MyPage,
]
