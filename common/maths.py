import numpy as np


def normalise_data(values):
    """Takes a series and returns a normalised series"""
    mean = values.mean()
    std = values.std()

    def calc(x, x_mean, x_std):
        return 1 /(1 + np.exp(-1 * ((x - x_mean) / x_std)))

    return values.apply(calc, args=(mean, std))