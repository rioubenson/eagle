import pandas as pd

def ticks_to_candle(data, time_frame, type='mid'):
    '''Expects a dataframe with a datetimeindex'''
    grouped = data.groupby('Instrument')
    bar = grouped[type].resample(time_frame, how='ohlc')
    return bar
