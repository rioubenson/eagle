import logging
import time

import numpy as np
import os
import pandas as pd
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis

from common.bars import ticks_to_candle
from common.maths import normalise_data
from event import SignalEvent
from settings import CSV_DATA_DIR

logger = logging.getLogger(__name__)


class OpenSignal(SignalEvent):
    open_time = 0


class Mustang(object):
    def __init__(self, instruments, events):
        self.instrument = instruments[0]
        self.events = events
        self.start_time = 0
        self.classifier = self.set_up_classifier()
        self.recent_ticks = pd.DataFrame()
        self.open_signals = []

    def get_data(self):
        pair_path = os.path.join(CSV_DATA_DIR, '%s_%s.csv' % (self.instrument, '1M'))
        data = pd.DataFrame.from_csv(pair_path)
        return data

    def set_up_classifier(self):
        historic_data = self.get_data()
        # Key is to identify a trend (use close for now)
        historic_data['return_5_timeframe'] = np.log(historic_data['Close'] / historic_data['Close'].shift(5)) * 100
        historic_data.fillna(0.0001, inplace=True)
        historic_data['vol_normalised'] = normalise_data(historic_data['Volume'])

        # Bucket Return
        def bucket_return(x, col):
            if 0 < x[col] < 0.02:
                return 1
            if 0.02 < x[col] < 0.1:
                return 2
            if x[col] > 0.1:
                return 3

            if 0 > x[col] > -0.02:
                return -1
            if -0.02 > x[col] > -0.1:
                return -2
            if x[col] < -0.1:
                return -3
            else:
                return 0

        historic_data['Return'] = historic_data.apply(bucket_return, axis=1, args=['return_5_timeframe'])

        historic_data['Move'] = historic_data['Close'] - historic_data['Open']

        # X as predictor values, with Y as the response
        x = historic_data[["Move"]]
        y = historic_data["Return"]

        model = QuadraticDiscriminantAnalysis()
        model.fit(x, y)
        return model

    def perform_prediction(self, bar):
        bar['move'] = bar['close'] - bar['open']
        prediction = self.classifier.predict(bar['move'])
        return prediction

    def calculate_signals(self, event):
        if event.type == 'TICK':
            if self.start_time == 0:
                self.start_time = event.time
            x = {'Instrument': [event.instrument],
                 'Time': [event.time],
                 'Bid': [float(event.bid)],
                 'Ask': [float(event.ask)],
                 'Mid': [float(event.mid)]}
            tick_df = pd.DataFrame(x)
            tick_df = tick_df.set_index(pd.DatetimeIndex(tick_df['Time']))
            del tick_df['Time']
            self.recent_ticks = self.recent_ticks.append(tick_df)
            if (event.time - self.start_time).total_seconds() > 60:
                bar = ticks_to_candle(self.recent_ticks, "1M", type="Mid")
                self.recent_ticks = pd.DataFrame()
                self.start_time = event.time
                future_return = self.perform_prediction(bar)[0]
                if future_return >= 2:
                    print "Entering LONG position"
                    signal = SignalEvent(event.instrument, "market", "buy", time.time())
                    self.events.put(signal)
                    open_signal = OpenSignal(signal.instrument, signal.order_type, signal.side, signal.time)
                    x = True
                    for s in self.open_signals:
                        if s.side == 'sell':
                            print "Already have an short pos, so closing it"
                            self.open_signals.remove(s)
                            x = False
                            continue
                    if x:
                        self.open_signals.append(open_signal)

                if future_return <= -2:
                    print "Entering SHORT position"
                    signal = SignalEvent(event.instrument, "market", "sell", time.time())
                    self.events.put(signal)
                    open_signal = OpenSignal(signal.instrument, signal.order_type, signal.side, signal.time)
                    x = True
                    for s in self.open_signals:
                        if s.side == 'buy':
                            print "Already have an open pos, so closing it"
                            self.open_signals.remove(s)
                            x = False
                            continue
                    if x:
                        self.open_signals.append(open_signal)

                # close any positions that have been open for 5 mins
                for signal in self.open_signals:
                    if signal.open_time == 5:
                        if signal.side == 'buy':
                            new_signal = SignalEvent(signal.instrument, 'market', 'sell', time.time())
                            self.events.put(new_signal)
                            self.open_signals.remove(signal)
                            print "Closing long pos after 5mins"
                        else:
                            new_signal = SignalEvent(signal.instrument, 'market', 'buy', time.time())
                            self.events.put(new_signal)
                            self.open_signals.remove(signal)
                            print "Closing short pos after 5mins"
                    else:
                        signal.open_time += 1
