import logging

class Trade(object):
    def __init__(self, time, units, type, open_px, label ):
        self.time = time
        self.units = units
        self.type = type
        self.open_px = open_px
        self.label = label

    def close_trade(self, time, px):
        self.close_time = time
        self.close_px = px

class TradeManager(object):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.trades=[]

