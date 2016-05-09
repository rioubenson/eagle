import pandas as pd


def awesome_indicator(historic_bars):
    """Calculates the Bill William's Awesome
    Indicator.  Takes a dataframe on bars for
    a given time frame and appends a column
    'awesome_indicator' to that bar"""
    historic_bars['median_price'] = (historic_bars['high'] + historic_bars['low']) / 2
    historic_bars['5_sma'] = pd.rolling_mean(historic_bars['median_price'], 5)
    historic_bars['34_sma'] = pd.rolling_mean(historic_bars['median_price'], 34)
    historic_bars['awesome_indicator'] = historic_bars['5_sma'] - historic_bars['34_sma']
    historic_bars.drop(['5_sma', '34_sma'])
    return historic_bars






