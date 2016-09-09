import pandas as pd

from common.maths import normalise_data


def simple_moving_average(values, timeframe, normalise=False):
    if normalise:
       result = normalise_data(pd.rolling_mean(values, timeframe, min_periods=1))
    else:
        result = pd.rolling_mean(values, timeframe, min_periods=1)
    return result

