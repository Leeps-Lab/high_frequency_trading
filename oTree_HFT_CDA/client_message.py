


class ClientMessage:
    """
    message types to communicate with
    client browsers
    """

    @staticmethod
    def spread_change(player_id, leg_up=None, leg_low=None):
        """
        default will 0 the spread
        """
        key = "SPRCHG"
        if not leg_up and not leg_low:
            value = {player_id: 0}
        else:
            value = {player_id: {"A": leg_up, "B": leg_low}}       
        msg = {key: value}
        return msg 
        
    @staticmethod
    def fund_p_change(new_price):
        key = "FPC"
        value = new_price
        msg = {key: value}
        return msg

    @staticmethod
    def execution(player_id, token, profit):
        key = "EXEC"
        value = { "id": player_id, "token": token, "profit": profit  }
        msg = {key: value}
        return msg

    @staticmethod
    def start_session():
        key = "SYNC"
        value = 0
        msg = {key: value}
        return msg
