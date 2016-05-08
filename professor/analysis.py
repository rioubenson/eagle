import os
import pandas as pd
import numpy as np
import matplotlib.pylab as plt
import datetime
import numpy as np
import pandas as pd
import sklearn

from pandas.io.data import DataReader
from sklearn.linear_model import LogisticRegression
from sklearn.lda import LDA
from sklearn.qda import QDA
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
        data['return_1_timeframe'] = np.log(data['Close'] / data['Close'].shift(1))* 100
        data['return_5_timeframe'] = np.log(data['Close'] / data['Close'].shift(5)) * 100
        data['return_10_timeframe'] = np.log(data['Close'] / data['Close'].shift(10)) * 100
        data.fillna(0, inplace=True)

        # Now add some moving averages
        SMAs = [5,9,20,50,100,200]
        for sma in SMAs:
            data = simple_moving_average(data, sma, 'Close')
            data['%sSmaRollingStdDev' % sma] = pd.rolling_std(data['Close'], sma, min_periods=1)
            data['%sSmaSD' % sma] = data['Close'] / data['%sSmaRollingStdDev' % sma]

        EMAs = [5, 9, 20, 50, 100, 200]
        for ema in EMAs:
            data["%sema" % str(ema)] = pd.ewma(data['Close'], span=ema)
            data['%sEmaRollingStdDev' % ema] = pd.rolling_std(data['Close'], ema, min_periods=1)

        returns = data[['return_10_timeframe']]
        ax = returns.plot()
        plt.show()

class Brain(Analysis):
    """Uses Machine Learning to identify predictive returns based on inputs"""

    def fit_model(self, name, model, X_train, y_train, X_test, pred):
        """Fits a classification model (for our purposes this is LR, LDA and QDA)
        using the training data, then makes a prediction and subsequent "hit rate"
        for the test data."""

        # Fit and predict the model on the training, and then test, data
        model.fit(X_train, y_train)
        pred[name] = model.predict(X_test)

        # Create a series with 1 being correct direction, 0 being wrong
        # and then calculate the hit rate based on the actual direction
        pred["%s_Correct" % name] = (1.0 + pred[name] * pred["Actual"]) / 2.0
        hit_rate = np.mean(pred["%s_Correct" % name])
        print "%s: %.3f" % (name, hit_rate)


    def create_lagged_series(self, data, lags=5):
        """This creates a pandas DataFrame that stores the percentage returns of the
        adjusted closing value of a stock obtained from Yahoo Finance, along with
        a number of lagged returns from the prior trading days (lags defaults to 5 days).
        Trading volume, as well as the Direction from the previous day, are also included."""

        # Create the new lagged DataFrame
        tslag = data
        tslag["Today"] = data["Close"]
        tslag["Volume"] = data["Volume"]

        # Create the shifted lag series of prior trading period close values
        for i in xrange(0, lags):
            tslag["Lag%s" % str(i + 1)] = data["Close"].shift(i + 1)

        # Create the returns DataFrame
        tsret = pd.DataFrame(index=tslag.index)
        tsret["Volume"] = tslag["Volume"]
        tsret["Today"] = tslag["Today"].pct_change() * 100.0

        # If any of the values of percentage returns equal zero, set them to
        # a small number (stops issues with QDA model in scikit-learn)
        for i, x in enumerate(tsret["Today"]):
            if (abs(x) < 0.0001):
                tsret["Today"][i] = 0.0001

        # Create the lagged percentage returns columns
        for i in xrange(0, lags):
            tsret["Lag%s" % str(i + 1)] = tslag["Lag%s" % str(i + 1)].pct_change() * 100.0

        # Create the "Direction" column (+1 or -1) indicating an up/down day
        tsret["Direction"] = np.sign(tsret["Today"])
        tsret.fillna(0, inplace=True)
        #tsret = tsret[tsret.index >= start_date]
        print tsret
        return tsret

    def start(self):
        # Create a lagged series of the S&P500 US stock market index
        data = self.get_data()
        snpret = self.create_lagged_series(data, lags=5)

        # Use the prior two days of returns as predictor values, with direction as the response
        X = snpret[["Lag1", "Lag2"]]
        y = snpret["Direction"]

        # The test data is split into two parts: Before and after 1st Jan 2005.
        start_test = datetime.datetime(2016, 04, 26)

        # Create training and test sets
        X_train = X[X.index < start_test]
        X_test = X[X.index >= start_test]
        y_train = y[y.index < start_test]
        y_test = y[y.index >= start_test]

        # Create prediction DataFrame
        pred = pd.DataFrame(index=y_test.index)
        pred["Actual"] = y_test

        # Create and fit the three models
        print "Hit Rates:"
        models = [("LR", LogisticRegression()), ("LDA", LDA()), ("QDA", QDA())]
        for m in models:
            self.fit_model(m[0], m[1], X_train, y_train, X_test, pred)


