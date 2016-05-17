import pandas as pd

from common.maths import normalise_data

def awesome_indicator(historic_bars, normalise=False):
    """Calculates the Bill William's Awesome
    Indicator.  Takes a dataframe on bars for
    a given time frame and appends a column
    'awesome_indicator' to that bar"""
    historic_bars['median_price'] = (historic_bars['High'] + historic_bars['Low']) / 2
    historic_bars['5_sma'] = pd.rolling_mean(historic_bars['median_price'], 5)
    historic_bars['34_sma'] = pd.rolling_mean(historic_bars['median_price'], 34)
    if normalise:
        historic_bars['awesome_indicator'] = normalise_data(historic_bars['5_sma'] - historic_bars['34_sma'])
    else:
        historic_bars['awesome_indicator'] = historic_bars['5_sma'] - historic_bars['34_sma']
    historic_bars.drop(['5_sma', '34_sma'], axis=1)
    return historic_bars






