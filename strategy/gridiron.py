import logging
import time

import pandas as pd

from common.ticks import get_tick_size
from event import SignalEvent
from strategy.strategy_base import Strategy


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
        self.stop_loss_buy = self.grid_mid - (tick_size * (get_grid_spacing() * 2))

        self.sell_level_one = self.grid_mid - (tick_size * (get_grid_spacing() * 2))
        self.sell_level_two = self.grid_mid - (tick_size * (get_grid_spacing() * 4))
        self.sell_level_three = self.grid_mid - (tick_size * (get_grid_spacing() * 6))
        self.sell_next_marker = self.grid_mid - (tick_size * (get_grid_spacing() * 8))
        self.stop_loss_sell = self.grid_mid + (tick_size * (get_grid_spacing() * 2))

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
        return "\n**************************************************************\n \
Current grid, mid: %s, buy1: %s, buy2: %s, TP: %s, SL: %s, sell1: %s, sell2: %s, TP: %s, SL: %s, LT: %s\n \
**************************************************************" \
               % (str(self.grid_mid), str(self.buy_level_one), str(self.buy_level_two), str(self.buy_next_marker),
                  str(self.stop_loss_buy), str(self.sell_level_one), str(self.sell_level_two),
                  str(self.sell_next_marker), str(self.stop_loss_sell), str(self.level_triggered))

    def __repr__(self):
        return str(self)


class GridIron(Strategy):
    def __init__(self, instrument, events, ):
        self.instrument = instrument
        self.events = events
        self.ticks = 0
        self.grid = None
        self.start_time = time.time()
        self.bars = pd.DataFrame()
        self.logger = logging.getLogger(__name__)

    def calculate_signals(self, event):
        if event.type == 'TICK':

            # Firstly dont do any thing until after 8am
            if 2 <= int(event.time.hour) < 20:
                if self.grid is None:
                    # Set up a grid
                    self.grid = Grid(self.instrument)
                    self.grid.start_grid(event.mid)
                else:
                    self.work_grid(event)
            if event.time.hour >= 20:
                if self.grid is not None and self.grid.level_triggered != 0:
                    signal = SignalEvent(event.instrument, "market", "close_all", time.time())
                    self.events.put(signal)
                    self.grid = None

    def new_bar(self, event):
        x = {'Instrument': [event.instrument],
             'Time': event.time,
             'high': [float(event.high)],
             'low': [float(event.low)],
             'open': [float(event.open)],
             'close': [float(event.close)]}

        df = pd.DataFrame(x)
        df = df.set_index(pd.DatetimeIndex(df['Time']))
        self.bars = pd.concat([self.bars, df])

    def work_grid(self, event):
        # If the mid has crossed the first buy, then generate a signal

        ##############################################################
        # LONG POSITION                                              #
        ##############################################################
        # LEVEL ONE
        if self.grid.level_triggered == 0 and event.mid > self.grid.buy_level_one:
            signal = SignalEvent(event.instrument, "market", "buy", time.time())
            self.logger.info("Opening position level 1 TREND, mid %s" % event.mid)
            self.events.put(signal)
            self.grid.shift_grid(1)

        # LEVEL TWO
        elif self.grid.level_triggered == 1 and event.mid > self.grid.buy_level_two:
            signal = SignalEvent(event.instrument, "market", "buy", time.time(), units_multiplier=0.25)
            self.events.put(signal)
            self.logger.info("Opening position level 2 TREND, mid %s" % event.mid)
            self.grid.shift_grid(1)

        # LEVEL THREE
        elif self.grid.level_triggered == 2 and event.mid > self.grid.buy_level_three:
            signal = SignalEvent(event.instrument, "market", "buy", time.time(), units_multiplier=0.1)
            self.events.put(signal)
            self.logger.info("Opening position level 3 TREND, mid %s" % event.mid)
            self.grid.shift_grid(1)

        # SHIFT GRID
        elif self.grid.level_triggered >= 3 and event.mid > self.grid.buy_next_marker:
            self.logger.info("Shifting new marker, mid %s" % event.mid)
            self.grid.shift_grid(1, True)
        # STOP LOSS
        elif self.grid.level_triggered > 0 and event.mid < self.grid.stop_loss_buy:
            signal = SignalEvent(event.instrument, "market", "close_all", time.time())
            self.events.put(signal)
            # if we have shifted grid this is profit taking
            if self.grid.level_triggered > 3:
                self.logger.info("Closing all buys to take profit, mid %s" % event.mid)
            else:
                self.logger.info( "Closing all buys at stop loss, mid %s" % event.mid)
            self.grid = None  # Done with this grid.

        ##############################################################
        # SHORT POSITION                                             #
        ##############################################################
        # If the mid has crossed the first sell, then generate a signal
        # LEVEL ONE
        elif self.grid.level_triggered == 0 and event.mid < self.grid.sell_level_one:
            signal = SignalEvent(event.instrument, "market", "sell", time.time())
            self.events.put(signal)
            self.logger.info("Opening position level -1 TREND, mid %s" % event.mid)
            self.grid.shift_grid(-1)
        # LEVEL TWO
        elif self.grid.level_triggered == -1 and event.mid < self.grid.sell_level_two:
            signal = SignalEvent(event.instrument, "market", "sell", time.time(), units_multiplier=0.25)
            self.events.put(signal)
            self.logger.info("Opening position level -2 TREND, mid %s" % event.mid)
            self.grid.shift_grid(-1)
        # LEVEL THREE
        elif self.grid.level_triggered == -2 and event.mid < self.grid.sell_level_three:
            signal = SignalEvent(event.instrument, "market", "sell", time.time(), units_multiplier=0.1)
            self.events.put(signal)
            self.logger.info("Opening position level -3 TREND, mid %s" % event.mid)
            self.grid.shift_grid(-1)
        # SHIFT GRID
        elif self.grid.level_triggered <= -3 and event.mid < self.grid.sell_next_marker:
            self.logger.info("Shifting grid, mid %s" % event.mid)
            self.grid.shift_grid(-1, True)
        # STOP LOSS
        elif self.grid.level_triggered < 0 and event.mid > self.grid.stop_loss_sell:
            signal = SignalEvent(event.instrument, "market", "close_all", time.time())
            self.events.put(signal)
            self.logger.info("Closing all sells stop loss, mid %s" % event.mid)
            self.grid = None  # Done with this grid.

        # LOG THE GRID FOR INFO Purposes
        if time.time() - self.start_time > 2:
            self.logger.info(self.grid)
            self.start_time = time.time()
