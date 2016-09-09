import time

from common.ticks import get_tick_size
from event.event import SignalEvent
import logging

logger = logging.getLogger(__name__)


def get_grid_spacing():
    return 2


class Grid(object):
    def __init__(self, instrument):
        self.instrument = instrument
        self.grid_mid = 0
        self.buy_level_one = 0
        self.buy_level_two = 0
        #self.take_profit_buy = 0
        self.stop_loss_buy = 0
        self.sell_level_one = 0
        self.sell_level_two = 0
        #self.take_profit_sell = 0
        self.stop_loss_sell = 0
        self.level_triggered = 0
        self.next_marker = 0

    def start_grid(self, mid_point):
        self.grid_mid = float(mid_point)
        tick_size = get_tick_size(self.instrument[0])
        # Change to volatility based
        self.buy_level_one = self.grid_mid + (tick_size * (get_grid_spacing() * 2))
        self.buy_level_two = self.grid_mid + (tick_size * (get_grid_spacing() * 4))
        self.buy_level_three = self.grid_mid + (tick_size * (get_grid_spacing() * 6))
        self.buy_next_marker = self.grid_mid + (tick_size * (get_grid_spacing() * 8))
        self.stop_loss_buy = self.grid_mid - (tick_size * (get_grid_spacing() * 4))

        self.sell_level_one = self.grid_mid - (tick_size * (get_grid_spacing() * 2))
        self.sell_level_two = self.grid_mid - (tick_size * (get_grid_spacing() * 4))
        self.sell_level_three = self.grid_mid - (tick_size * (get_grid_spacing() * 6))
        self.sell_next_marker = self.grid_mid - (tick_size * (get_grid_spacing() * 8))
        self.stop_loss_sell = self.grid_mid + (tick_size * (get_grid_spacing() * 4))

    def shift_grid(self, direction, shift_marker=False):
        tick_size = get_tick_size(self.instrument[0])
        if direction > 0:
            self.stop_loss_buy += (tick_size * (get_grid_spacing() * 2))
            self.level_triggered += 1
            if shift_marker:
                self.buy_next_marker += (tick_size * (get_grid_spacing() * 2))
        elif direction < 0:
            self.stop_loss_sell -= (tick_size * (get_grid_spacing() * 2))
            self.level_triggered -= 1
            if shift_marker:
                self.sell_next_marker -= (tick_size * (get_grid_spacing() * 2))

    def __str__(self):
        return "Current grid, mid: %s, buy1: %s, buy2: %s, TP: %s, SL: %s, sell1: %s, sell2: %s, TP: %s, SL: %s, LT: %s" \
               % (str(self.grid_mid), str(self.buy_level_one), str(self.buy_level_two), str(self.buy_next_marker),
                  str(self.stop_loss_buy), str(self.sell_level_one), str(self.sell_level_two),
                  str(self.sell_next_marker), str(self.stop_loss_sell), str(self.level_triggered))

    def __repr__(self):
        return str(self)


class GridIron(object):
    def __init__(self, instrument, events, ):
        self.instrument = instrument
        self.events = events
        self.ticks = 0
        self.grid = None
        self.start_time = time.time()

    def calculate_signals(self, event):
        if event.type == 'TICK':

            # Firstly dont do any thing until after 8am
            if 8 < int(event.time.hour) < 20:
                if self.grid is None:
                    # Set up a grid
                    self.grid = Grid(self.instrument)
                    self.grid.start_grid(event.mid)
                else:
                    self.check_grid(event)
            if event.time.hour > 20:
                if self.grid is not None and self.grid.level_triggered != 0:
                    signal = SignalEvent(event.instrument, "market", "close_all", time.time())
                    self.events.put(signal)
                    self.grid = None

    def check_grid(self, event):
        # If the mid has crossed the first buy, then generate a signal

        # LEVEL ONE
        if self.grid.level_triggered == 0 and event.mid > self.grid.buy_level_one:
            signal = SignalEvent(event.instrument, "market", "buy", time.time())
            print "Opening position level 1 TREND, mid %s" % event.mid
            self.events.put(signal)
            self.grid.shift_grid(1)

        # LEVEL TWO
        elif self.grid.level_triggered == 1 and event.mid > self.grid.buy_level_two:
            signal = SignalEvent(event.instrument, "market", "buy", time.time(), units_multiplier=0.5)
            self.events.put(signal)
            print "Opening position level 2 TREND, mid %s" % event.mid
            self.grid.shift_grid(1)

        elif self.grid.level_triggered == 2 and event.mid > self.grid.buy_level_three:
            signal = SignalEvent(event.instrument, "market", "buy", time.time(), units_multiplier=0.25)
            self.events.put(signal)
            print "Opening position level 3 TREND, mid %s" % event.mid
            self.grid.shift_grid(1)
        elif self.grid.level_triggered >= 3 and event.mid > self.grid.buy_next_marker:
            print "Shifting new marker, mid %s" % event.mid
            self.grid.shift_grid(1, True)

        elif self.grid.level_triggered > 0 and event.mid < self.grid.stop_loss_buy:
            signal = SignalEvent(event.instrument, "market", "close_all", time.time())
            self.events.put(signal)
            print "Closing all buys at stop loss, mid %s" % event.mid
            self.grid = None  # Done with this grid.


        # If the mid has crossed the first sell, then generate a signal
        elif self.grid.level_triggered == 0 and event.mid < self.grid.sell_level_one:
            signal = SignalEvent(event.instrument, "market", "sell", time.time())
            self.events.put(signal)
            print "Opening position level -1 TREND, mid %s" % event.mid
            self.grid.shift_grid(-1)

        elif self.grid.level_triggered == -1 and event.mid < self.grid.sell_level_two:
            signal = SignalEvent(event.instrument, "market", "sell", time.time(), units_multiplier=0.5)
            self.events.put(signal)
            print "Opening position level -2 TREND, mid %s" % event.mid
            self.grid.shift_grid(-1)
        elif self.grid.level_triggered == -2 and event.mid < self.grid.sell_level_three:
            signal = SignalEvent(event.instrument, "market", "sell", time.time(), units_multiplier=0.25)
            self.events.put(signal)
            print "Opening position level -3 TREND, mid %s" % event.mid
            self.grid.shift_grid(-1)
        elif self.grid.level_triggered <= -3 and event.mid < self.grid.sell_next_marker:
            print "Shifting grid, mid %s" % event.mid
            self.grid.shift_grid(-1, True)
        elif self.grid.level_triggered < 0 and event.mid > self.grid.stop_loss_sell:
            signal = SignalEvent(event.instrument, "market", "close_all", time.time())
            self.events.put(signal)
            print "Closing all sells stop loss, mid %s" % event.mid
            self.grid = None  # Done with this grid.

        if time.time() - self.start_time > 2:
            print self.grid
            self.start_time = time.time()
