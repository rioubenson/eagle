import pandas as pd

from settings import OUTPUT_RESULTS_DIR


class History(object):
    """Object for holding history of trades
    for performance analysis"""

    def __init__(self, instrument, currency):
        self.instrument = instrument
        self.currency = currency
        self.trades = []

    def get_history(self):
        variables = self.trades[0].keys()
        df = pd.DataFrame([[getattr(i, j) for j in variables] for i in self.trades], columns=variables)
        return df

    def print_history(self):
        variables = self.trades[0].keys()
        df = pd.DataFrame([[getattr(i, j) for j in variables] for i in self.trades], columns=variables)
        df.to_csv(OUTPUT_RESULTS_DIR + '')
