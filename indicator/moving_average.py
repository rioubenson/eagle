import pandas as pd


def simple_moving_average(data, timeframe, column_to_calculate):
    column = "%sSMA" % str(timeframe)
    data[column] = pd.rolling_mean(data[column_to_calculate], timeframe, min_periods=1)
    return data