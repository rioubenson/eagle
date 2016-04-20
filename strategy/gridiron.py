import time


from common.ticks import get_tick_size
from event.event import SignalEvent


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
        self.grid_mid = mid_point
        # Change to volatility based
        self.buy_level_one = mid_point + (get_tick_size(self.instrument) * 2)
        self.buy_level_two = mid_point + (get_tick_size(self.instrument) * 4)
        self.take_profit_buy = mid_point + (get_tick_size(self.instrument) * 6)
        self.stop_loss_buy = mid_point - (get_tick_size(self.instrument) * 2)

        self.sell_level_one = mid_point - (get_tick_size(self.instrument) * 2)
        self.sell_level_two = mid_point - (get_tick_size(self.instrument) * 4)
        self.take_profit_sell = mid_point - (get_tick_size(self.instrument) * 6)
        self.stop_loss_sell = mid_point + (get_tick_size(self.instrument) * 2)

    def shift_grid(self, direction):
        if direction > 0:
            self.stop_loss_buy += (get_tick_size(self.instrument) * 2)
            self.level_triggered += 1
        elif direction < 0:
            self.stop_loss_sell -= (get_tick_size(self.instrument) * 2)
            self.level_triggered -= 1


class GridIron(object):
    def __init__(self, instrument, events):
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
            else:
                # If the mid has crossed the first buy, then generate a signal
                if self.grid.level_triggered == 0 and event.mid > self.grid.buy_level_one:
                    signal = SignalEvent(self.instrument, "market", "buy", time.time())
                    self.events.put(signal)
                    self.grid.shift_grid(1)
                elif self.grid.level_triggered == 1 and event.mid > self.grid.buy_level_two:
                    signal = SignalEvent(self.instrument, "market", "buy", time.time())
                    self.events.put(signal)
                    self.grid.shift_grid(1)
                elif self.grid.level_triggered == 2 and event.mid > self.grid.take_profit_buy:
                    signal = SignalEvent(self.instrument, "market", "close_all", time.time())
                    self.events.put(signal)
                    self.grid = None # Done with this grid.
                elif self.grid.level_triggered > 0 and event.mid < self.grid.stop_loss_buy:
                    signal = SignalEvent(self.instrument, "market", "close_all", time.time())
                    self.events.put(signal)
                    self.grid = None  # Done with this grid.
                # If the mid has crossed the first sell, then generate a signal
                elif self.grid.level_triggered == 0 and event.mid < self.grid.sell_level_one:
                    signal = SignalEvent(self.instrument, "market", "sell", time.time())
                    self.events.put(signal)
                    self.grid.shift_grid(-1)
                elif self.grid.level_triggered == -1 and event.mid < self.grid.sell_level_two:
                    signal = SignalEvent(self.instrument, "market", "sell", time.time())
                    self.events.put(signal)
                    self.grid.shift_grid(-1)
                elif self.grid.level_triggered == -2 and event.mid > self.grid.take_profit_sell:
                    signal = SignalEvent(self.instrument, "market", "close_all", time.time())
                    self.events.put(signal)
                    self.grid = None  # Done with this grid.
                elif self.grid.level_triggered < 0 and event.mid > self.grid.stop_loss_sell:
                    signal = SignalEvent(self.instrument, "market", "close_all", time.time())
                    self.events.put(signal)
                    self.grid = None  # Done with this grid.
