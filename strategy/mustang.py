import logging

import time

import os
import pandas as pd
import numpy as np
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis

from common.bars import ticks_to_candle
from common.maths import normalise_data
from settings import CSV_DATA_DIR

logger = logging.getLogger(__name__)


class Mustang(object):
    def __init__(self, instruments, events ):
        self.instrument = instruments[0]
        self.events = events
        self.start_time = time.time()
        self.classifier = self.set_up_classifier()
        self.recent_ticks = pd.DataFrame()

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
        x = historic_data[["Move", "vol_normalised"]]
        y = historic_data["Return"]

        model = LinearDiscriminantAnalysis()
        model.fit(x, y)
        return model

    def calculate_signals(self, event):
        if event.type == 'TICK':
            x = {'Instrument': [event.instrument],
                 'Time': [event.time],
                 'Bid': [float(event.bid)],
                 'Ask': [float(event.ask)],
                 'Mid': [float(event.mid)]}
            tick_df = pd.DataFrame(x)
            tick_df = tick_df.set_index(pd.DatetimeIndex(tick_df['Time']))
            del tick_df['Time']
            self.recent_ticks = self.recent_ticks.append(tick_df)
            if time.time() - self.start_time > 1:
                bar = ticks_to_candle(self.recent_ticks, "1M", type="Mid")
                self.recent_ticks = pd.DataFrame()
                self.start_time = time.time()
                print bar

