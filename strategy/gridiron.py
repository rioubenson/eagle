import time

from common.bars import ticks_to_candle
from common.ticks import get_tick_size
from event.event import SignalEvent
import logging
import pandas as pd

from indicator.indicator import STDDEV
from indicator.indicator import WVF

logger = logging.getLogger(__name__)


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
        tick_size = get_tick_size(self.instrument[0])
        # Change to volatility based
        self.buy_level_one = self.grid_mid + (tick_size * (get_grid_spacing() * 2))
        self.buy_level_two = self.grid_mid + (tick_size * (get_grid_spacing() * 4))
        self.buy_level_three = self.grid_mid + (tick_size * (get_grid_spacing() * 6))
        self.take_profit_buy = self.grid_mid + (tick_size * (get_grid_spacing() * 8))
        self.stop_loss_buy = self.grid_mid - (tick_size * (get_grid_spacing() * 2))

        self.sell_level_one = self.grid_mid - (tick_size * (get_grid_spacing() * 2))
        self.sell_level_two = self.grid_mid - (tick_size * (get_grid_spacing() * 4))
        self.sell_level_three = self.grid_mid - (tick_size * (get_grid_spacing() * 6))
        self.take_profit_sell = self.grid_mid - (tick_size * (get_grid_spacing() * 8))
        self.stop_loss_sell = self.grid_mid + (tick_size * (get_grid_spacing() * 2))

    def shift_grid(self, direction):
        tick_size = get_tick_size(self.instrument[0])
        if direction > 0:
            self.stop_loss_buy += (tick_size * (get_grid_spacing() * 2))
            self.level_triggered += 1
        elif direction < 0:
            self.stop_loss_sell -= (tick_size * (get_grid_spacing() * 2))
            self.level_triggered -= 1

    def __str__(self):
        return "Current grid, mid: %s, buy1: %s, buy2: %s, TP: %s, SL: %s, sell1: %s, sell2: %s, TP: %s, SL: %s, LT: %s" \
               % (str(self.grid_mid), str(self.buy_level_one), str(self.buy_level_two), str(self.take_profit_buy),
                  str(self.stop_loss_buy), str(self.sell_level_one), str(self.sell_level_two),
                  str(self.take_profit_sell), str(self.stop_loss_sell), str(self.level_triggered))

    def __repr__(self):
        return str(self)


class GridIron(object):
    def __init__(self, instrument, events, ):
        self.instrument = instrument
        self.events = events
        self.candles = pd.DataFrame()
        self.recent_ticks = pd.DataFrame()
        self.grid = None
        self.start_time = time.time()
        self.first_tick_time = None
        self.trading = False

    def calculate_signals(self, event):
        if event.type == 'TICK':
            # Firstly dont do any thing until after 8am
            if self.first_tick_time is None:
                self.first_tick_time = event.time
            x = {'Instrument': [event.instrument],
                 'Time': [event.time],
                 'Bid': [float(event.bid)],
                 'Ask': [float(event.ask)],
                     'Mid': [float(event.mid)]}
            tick_df = pd.DataFrame(x)
            tick_df = tick_df.set_index(pd.DatetimeIndex(tick_df['Time']))
            del tick_df['Time']
            self.recent_ticks = self.recent_ticks.append(tick_df)

            if (event.time - self.first_tick_time).total_seconds() > 60:
                candle = ticks_to_candle(self.recent_ticks, "1Min", type="Mid")
                self.first_tick_time = None
                self.recent_ticks = pd.DataFrame()
                self.candles = pd.concat([self.candles, candle])
                self.candles = WVF(self.candles)
                self.candles.fillna('ffill')
                #self.candles = STDDEV(self.candles)

            if not self.candles.empty:
                current_wvf = self.candles.tail(1)['wvf'].iloc[0]
            else:
                current_wvf = 0

            if 3 < int(event.time.hour) < 20:

                if self.grid is None:

                    #    print "Creating Grid: %s" % current_wvf
                        # Set up a grid
                    self.grid = Grid(self.instrument)
                    self.grid.start_grid(event.mid)
                else:
                    self.work_grid(event)
            if event.time.hour > 20:
                if self.grid is not None:
                    signal = SignalEvent(event.instrument, "market", "close_all", time.time())
                    self.events.put(signal)

    def work_grid(self, event):
        # If the mid has crossed the first buy, then generate a signal
        if self.grid.level_triggered == 0 and event.mid > self.grid.buy_level_one:
            signal = SignalEvent(event.instrument, "market", "buy", time.time())
            print "Opening position level 1 mid %s" % event.mid
            if self.trading:
                self.events.put(signal)
            self.grid.shift_grid(1)

        elif self.grid.level_triggered == 1 and event.mid > self.grid.buy_level_two:
            signal = SignalEvent(event.instrument, "market", "buy", time.time(), units_multiplier=0.5)
            if self.trading:
                self.events.put(signal)
            print "Opening position level 2 mid %s" % event.mid
            self.grid.shift_grid(1)

        elif self.grid.level_triggered == 2 and event.mid > self.grid.buy_level_three:
            signal = SignalEvent(event.instrument, "market", "buy", time.time(), units_multiplier=0.25)
            if self.trading:
                self.events.put(signal)
            print "Opening position level 3 mid %s" % event.mid
            self.grid.shift_grid(1)
            self.trading = True

        # TAKE PROFIT
        elif self.grid.level_triggered == 3 and event.mid > self.grid.take_profit_buy:
            signal = SignalEvent(event.instrument, "market", "close_all", time.time())
            if self.trading:
                self.events.put(signal)
            print "Closing all buys to take profit, mid %s" % event.mid
            self.grid = None  # Done with this grid.

        # STOP LOSS
        elif self.grid.level_triggered > 0 and event.mid < self.grid.stop_loss_buy:
            signal = SignalEvent(event.instrument, "market", "close_all", time.time())
            if self.trading:
                self.events.put(signal)
            print "Closing all buys at stop loss, mid %s" % event.mid
            self.grid = None  # Done with this grid.
            self.trading = False
        # If the mid has crossed the first sell, then generate a signal
        elif self.grid.level_triggered == 0 and event.mid < self.grid.sell_level_one:
            signal = SignalEvent(event.instrument, "market", "sell", time.time())
            if self.trading:
                self.events.put(signal)
            print "Opening position level -1, mid %s" % event.mid
            self.grid.shift_grid(-1)

        elif self.grid.level_triggered == -1 and event.mid < self.grid.sell_level_two:
            signal = SignalEvent(event.instrument, "market", "sell", time.time(), units_multiplier=0.5)
            if self.trading:
                self.events.put(signal)
            print "Opening position level -2 TREND, mid %s" % event.mid
            self.grid.shift_grid(-1)

        elif self.grid.level_triggered == -2 and event.mid < self.grid.sell_level_three:
            signal = SignalEvent(event.instrument, "market", "sell", time.time(), units_multiplier=0.25)
            if self.trading:
                self.events.put(signal)
            print "Opening position level -3 TREND, mid %s" % event.mid
            self.grid.shift_grid(-1)
            self.trading = True

        elif self.grid.level_triggered == -3 and event.mid < self.grid.take_profit_sell:
            signal = SignalEvent(event.instrument, "market", "close_all", time.time())
            if self.trading:
                self.events.put(signal)
            print "Closing all sells to take profit, mid %s" % event.mid
            self.grid = None  # Done with this grid.

        elif self.grid.level_triggered < 0 and event.mid > self.grid.stop_loss_sell:
            signal = SignalEvent(event.instrument, "market", "close_all", time.time())
            if self.trading:
                self.events.put(signal)
            print "Closing all sells stop loss, mid %s" % event.mid
            self.grid = None  # Done with this grid.
            self.trading = False
        if time.time() - self.start_time > 2:
            print self.grid
            self.start_time = time.time()
