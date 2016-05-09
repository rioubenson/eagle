import pandas as pd

from common.maths import normalise_data


def simple_moving_average(data, timeframe, column_to_calculate, normalise=False):
    column = "%sSMA" % str(timeframe)
    if normalise:
        data[column] = normalise_data(pd.rolling_mean(data[column_to_calculate], timeframe, min_periods=1))
    else:
        data[column] = pd.rolling_mean(data[column_to_calculate], timeframe, min_periods=1)
    return data