import os
import pandas as pd
import numpy as np
import matplotlib.pylab as plt
import datetime
import numpy as np
import pandas as pd
import sklearn

from pandas.io.data import DataReader
from sklearn.linear_model import *
from sklearn.lda import LDA
from sklearn.qda import QDA

from common.maths import normalise_data
from indicator.moving_average import simple_moving_average
from settings import CSV_DATA_DIR


class Analysis(object):

    def __init__(self, instrument, time_frame):
        self.instrument = instrument
        self.time_frame = time_frame

    def get_data(self):
        pair_path = os.path.join(CSV_DATA_DIR, '%s_%s.csv' % (self.instrument, self.time_frame))
        data = pd.DataFrame.from_csv(pair_path)
        return data


class Trendy(Analysis):
    """Tries to identify best ways of identifying trends"""

    def start(self):

        # Firstly pull in the data
        data = self.get_data()

        overall_stats_close = data['Close'].describe()
        close_std = overall_stats_close['std']

        # Key is to identify a trend (use close for now)
        #data['return_1_timeframe'] = np.log(data['Close'] / data['Close'].shift(1))* 100
        data['return_5_timeframe'] = np.log(data['Close'] / data['Close'].shift(5)) * 100
        #data['return_10_timeframe'] = np.log(data['Close'] / data['Close'].shift(10)) * 100
        data.fillna(0.0001, inplace=True)
        data['vol_normalised'] = normalise_data(data['Volume'])
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

        data['Return'] = data.apply(bucket_return, axis=1, args=['return_5_timeframe'])
        # Now add some moving averages
        #smas = [9,200]
        #for sma in smas:
        #    data = simple_moving_average(data, sma, 'Close', normalise=True)

        data['Move'] = data['Close'] - data['Open']
        """
        EMAs = [5, 9, 20, 50, 100, 200]
        for ema in EMAs:
            data["%sema" % str(ema)] = pd.ewma(data['Close'], span=ema)
            data['%sEmaRollingStdDev' % ema] = pd.rolling_std(data['Close'], ema, min_periods=1)
        """

        # X as predictor values, with Y as the response
        X = data[[ "Move", "vol_normalised"]]
        y = data["Return"]

        # The test data is split into two parts: Before and after 1st Jan 2005.
        start_test = datetime.datetime(2016, 04, 26)

        # Create training and test sets
        x_train = X[X.index < start_test]
        x_test = X[X.index >= start_test]
        y_train = y[y.index < start_test]
        y_test = y[y.index >= start_test]

        brain = Brain(x_train, x_test, y_train, y_test)

        brain.perform_regression_analysis()


class Brain():
    """Uses Machine Learning to identify predictive returns based on inputs"""

    def __init__(self, X_train, X_test, Y_train, Y_test):
        self.x_train = X_train
        self.x_test = X_test
        self.y_train = Y_train
        self.y_test = Y_test

    def fit_model(self, name, model, X_train, y_train, X_test, pred):
        """Fits a classification model using the training data,
        then makes a prediction and subsequent "hit rate"
        for the test data."""

        # Fit and predict the model on the training, and then test, data
        model.fit(X_train, y_train)
        pred[name] = model.predict(X_test)

        # Create a series with 1 being correct direction, 0 being wrong
        # and then calculate the hit rate based on the actual direction
        pred["%s_Correct" % name] = (1.0 + pred[name] * pred["Actual"]) / 2.0
        hit_rate = np.mean(pred["%s_Correct" % name])

        print "%s: %.3f" % (name, hit_rate)

    def perform_regression_analysis(self):
        """
        Performs a number of different regression techniques to try to predict
        value
        """
        # Create prediction DataFrame
        pred = pd.DataFrame(index=self.y_test.index)
        pred["Actual"] = self.y_test

        # Create and fit the three models
        print "Hit Rates:"
        models = linear
        for m in models:
            try:
                self.fit_model(str(m), m(), self.x_train, self.y_train, self.x_test, pred)
            except ValueError:
                print "Not able to do %s" % str(m)


linear = [LogisticRegression,
          LDA,
         QDA,
         # LassoLars,
         # LassoLarsCV,
         # LassoLarsIC,
         # LinearRegression,
         # Ridge,
         # RidgeCV,
         # SGDRegressor,
         # TheilSenRegressor,
            ]