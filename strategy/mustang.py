import logging

import time
import pandas as pd
from settings import CSV_DATA_DIR

logger = logging.getLogger(__name__)

class Mustang(object):
    def __init__(self, instrument, events, ):
        self.instrument = instrument
        self.events = events
        self.start_time = time.time()
        self.classifier = self.set_up_classifier()

    def get_data(self):
        pair_path = os.path.join(CSV_DATA_DIR, '%s_%s.csv' % (self.instrument, self.time_frame))
        data = pd.DataFrame.from_csv(pair_path)
        return data

    def set_up_classifier(self):
        historic_data = self.get_data()


    def calculate_signals(self, event):
        if event.type == 'TICK':

                # If the mid has crossed the first buy, then generate a signal
                if self.grid.level_triggered == 0 and event.mid > self.grid.buy_level_one:
                    signal = SignalEvent(event.instrument, "market", "sell", time.time())
                    self.events.put(signal)
                    self.grid.shift_grid(1)
                elif self.grid.level_triggered == 1 and event.mid > self.grid.buy_level_two:
                    signal = SignalEvent(event.instrument, "market", "sell", time.time())
                    self.events.put(signal)
                    self.grid.shift_grid(1)
                elif self.grid.level_triggered == 2 and event.mid > self.grid.take_profit_buy:
                    signal = SignalEvent(event.instrument, "market", "close_all", time.time())
                    self.events.put(signal)
                    self.grid = None # Done with this grid.
                elif self.grid.level_triggered > 0 and event.mid < self.grid.stop_loss_buy:
                    signal = SignalEvent(event.instrument, "market", "close_all", time.time())
                    self.events.put(signal)
                    self.grid = None  # Done with this grid.
                # If the mid has crossed the first sell, then generate a signal
                elif self.grid.level_triggered == 0 and event.mid < self.grid.sell_level_one:
                    signal = SignalEvent(event.instrument, "market", "buy", time.time())
                    self.events.put(signal)
                    self.grid.shift_grid(-1)
                elif self.grid.level_triggered == -1 and event.mid < self.grid.sell_level_two:
                    signal = SignalEvent(event.instrument, "market", "buy", time.time())
                    self.events.put(signal)
                    self.grid.shift_grid(-1)
                elif self.grid.level_triggered == -2 and event.mid > self.grid.take_profit_sell:
                    signal = SignalEvent(event.instrument, "market", "close_all", time.time())
                    self.events.put(signal)
                    self.grid = None  # Done with this grid.
                elif self.grid.level_triggered < 0 and event.mid > self.grid.stop_loss_sell:
                    signal = SignalEvent(event.instrument, "market", "close_all", time.time())
                    self.events.put(signal)
                    self.grid = None  # Done with this grid.

            if time.time() - self.start_time > 2:
                print self.grid
                self.start_time = time.time()