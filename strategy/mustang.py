import logging

import time

import os
import pandas as pd
from settings import CSV_DATA_DIR

logger = logging.getLogger(__name__)

class Mustang(object):
    def __init__(self, instrument, events, ):
        self.instrument = instrument
        self.events = events
        self.start_time = time.time()
        self.classifier = self.set_up_classifier()
        self.recent_ticks = pd.DataFrame()

    def get_data(self):
        pair_path = os.path.join(CSV_DATA_DIR, '%s_%s.csv' % (self.instrument, self.time_frame))
        data = pd.DataFrame.from_csv(pair_path)
        return data

    def set_up_classifier(self):
        historic_data = self.get_data()


    def calculate_signals(self, event):
        if event.type == 'TICK':
            tick_df = pd.DataFrame([event.instrument, event.time, event.bid, event.ask, event.mid], columns=['Instrument',
                                                                                                             'time',
                                                                                                             'bid',
                                                                                                             'ask',
                                                                                                             'mid'])
            tick
            self.recent_ticks.append()
            if time.time() - self.start_time()
