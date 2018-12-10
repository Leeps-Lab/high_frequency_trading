

class TradeSession:

    def __init__(self):
        self.markets = {}
        self.subprocesses = {}
        self.trading_markets = []

    def register_market(self, market_id, market_format):
        self.markets[market_id] = market_format
    
    def start_trade(self, market_id=None):
        pass
    
    def stop_trade();
        pass
    
    def spawn_subprocess():
        pass
    
    def kill_subprocess():
        pass
        

