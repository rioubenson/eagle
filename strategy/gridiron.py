import time


from common.ticks import get_tick_size
from event.event import SignalEvent

def get_grid_spacing():
    return 2

class Grid(object):
    def __init__(self, instrument):
        self.instrument = instrument
        self.grid_mid = 0
        self.buy_level_one = 0
        self.buy_level_two = 0
        self.take_profit_buy = 0
        self.stop_loss_buy = 0
        self.sell_level_one = 0
        self.sell_level_two = 0
        self.take_profit_sell = 0
        self.stop_loss_sell = 0
        self.level_triggered = 0

    def start_grid(self, mid_point):
        self.grid_mid = float(mid_point)
        # Change to volatility based
        self.buy_level_one = self.grid_mid + (get_tick_size(self.instrument) * (get_grid_spacing() * 2))
        self.buy_level_two = self.grid_mid + (get_tick_size(self.instrument) * (get_grid_spacing() * 4))
        self.take_profit_buy = self.grid_mid + (get_tick_size(self.instrument) * (get_grid_spacing() * 6))
        self.stop_loss_buy = self.grid_mid - (get_tick_size(self.instrument) * (get_grid_spacing() * 4))

        self.sell_level_one = self.grid_mid - (get_tick_size(self.instrument) * (get_grid_spacing() * 2))
        self.sell_level_two = self.grid_mid - (get_tick_size(self.instrument) * (get_grid_spacing() * 4))
        self.take_profit_sell = self.grid_mid - (get_tick_size(self.instrument) * (get_grid_spacing() * 6))
        self.stop_loss_sell = self.grid_mid + (get_tick_size(self.instrument) * (get_grid_spacing() * 4))


    def shift_grid(self, direction):
        if direction > 0:
            self.stop_loss_buy += (get_tick_size(self.instrument) * 2)
            self.level_triggered += 1
        elif direction < 0:
            self.stop_loss_sell -= (get_tick_size(self.instrument) * 2)
            self.level_triggered -= 1



    def __str__(self):
        return "Current grid, mid: %s, buy1: %s, buy2: %s, TP: %s, SL: %s, sell1: %s, sell2: %s, TP: %s, SL: %s, LT: %s" \
                  % (str(self.grid_mid), str(self.buy_level_one), str(self.buy_level_two), str(self.take_profit_buy),
                    str(self.stop_loss_buy), str(self.sell_level_one), str(self.sell_level_two),
                    str(self.take_profit_sell), str(self.stop_loss_sell), str(self.level_triggered))


    def __repr__(self):
        return str(self)

def __repr__(self):
    return str(self)
class GridIron(object):
    def __init__(self, instrument, events, ):
        self.instrument = instrument
        self.events = events
        self.ticks = 0
        self.grid = None

    def calculate_signals(self, event):
        if event.type == 'TICK':
            if self.grid is None:
                # Set up a grid
                self.grid = Grid(self.instrument)
                self.grid.start_grid(event.mid)
                #print self.grid
            else:
                # If the mid has crossed the first buy, then generate a signal
                if self.grid.level_triggered == 0 and event.mid > self.grid.buy_level_one:
                    signal = SignalEvent(event.instrument, "market", "buy", time.time())
                    self.events.put(signal)
                    self.grid.shift_grid(1)
                    print self.grid
                elif self.grid.level_triggered == 1 and event.mid > self.grid.buy_level_two:
                    signal = SignalEvent(event.instrument, "market", "buy", time.time())
                    self.events.put(signal)
                    self.grid.shift_grid(1)
                    print self.grid
                elif self.grid.level_triggered == 2 and event.mid > self.grid.take_profit_buy:
                    signal = SignalEvent(event.instrument, "market", "close_all", time.time())
                    self.events.put(signal)
                    print "Taking profit"
                    self.grid = None # Done with this grid.
                elif self.grid.level_triggered > 0 and event.mid < self.grid.stop_loss_buy:
                    signal = SignalEvent(event.instrument, "market", "close_all", time.time())
                    self.events.put(signal)
                    print "Stop Loss"
                    self.grid = None  # Done with this grid.
                # If the mid has crossed the first sell, then generate a signal
                elif self.grid.level_triggered == 0 and event.mid < self.grid.sell_level_one:
                    signal = SignalEvent(event.instrument, "market", "sell", time.time())
                    self.events.put(signal)
                    self.grid.shift_grid(-1)
                    print self.grid
                elif self.grid.level_triggered == -1 and event.mid < self.grid.sell_level_two:
                    signal = SignalEvent(event.instrument, "market", "sell", time.time())
                    self.events.put(signal)
                    self.grid.shift_grid(-1)
                    print self.grid
                elif self.grid.level_triggered == -2 and event.mid > self.grid.take_profit_sell:
                    signal = SignalEvent(event.instrument, "market", "close_all", time.time())
                    self.events.put(signal)
                    print "Taking profit"
                    self.grid = None  # Done with this grid.
                elif self.grid.level_triggered < 0 and event.mid > self.grid.stop_loss_sell:
                    signal = SignalEvent(event.instrument, "market", "close_all", time.time())
                    self.events.put(signal)
                    self.grid = None  # Done with this grid.
                    print "Stop Loss"