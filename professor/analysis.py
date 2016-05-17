import itertools
import numpy as np
import os
import pandas as pd

from common.maths import normalise_data
from indicator.awesome_indicator import awesome_indicator
from indicator.indicator import *
from settings import CSV_DATA_DIR
from sklearn.lda import LDA
from sklearn.linear_model import *
from sklearn.qda import QDA


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

    def create_lagged_series(self, ts, lags=5):
        """This creates a pandas DataFrame that stores the percentage returns of the
        adjusted closing value of a stock obtained from Yahoo Finance, along with
        a number of lagged returns from the prior trading days (lags defaults to 5 days).
        Trading volume, as well as the Direction from the previous day, are also included."""

        # Create the new lagged DataFrame
        tslag = pd.DataFrame(index=ts.index)
        tslag["Close"] = ts["Close"]
        tslag["Volume"] = ts["Volume"]

        # Create the shifted lag series of prior trading period close values
        for i in xrange(0, lags):
            tslag["Lag%s" % str(i + 1)] = ts["Close"].shift(i + 1)

        # Create the returns DataFrame
        tsret = pd.DataFrame(index=tslag.index)
        tsret["Volume"] = tslag["Volume"]
        tsret["Return"] = tslag["Close"].pct_change() * 100.0

        # If any of the values of percentage returns equal zero, set them to
        # a small number (stops issues with QDA model in scikit-learn)
        for i, x in enumerate(tsret["Return"]):
            if (abs(x) < 0.0001):
                tsret["Return"][i] = 0.0001

        # Create the lagged percentage returns columns
        for i in xrange(0, lags):
            tsret["Lag%s" % str(i + 1)] = tslag["Lag%s" % str(i + 1)].pct_change() * 100.0

        return tsret

    def start(self):

        # Firstly pull in the data
        data = self.get_data()

        # clean data
        data = data[data['Volume'] != 0]

        overall_stats_close = data['Close'].describe()
        close_std = overall_stats_close['std']

        # Bucket Return
        def bucket_return(x, col):
            if 0 < x[col] < 0.02:  # weak trend
                return 1
            if 0.02 < x[col] < 0.1:  # decent trend
                return 2
            if x[col] > 0.1:  # strong trend
                return 3

            if 0 > x[col] > -0.02:
                return -1
            if -0.02 > x[col] > -0.1:
                return -2
            if x[col] < -0.1:
                return -3
            else:
                return 0

        # Now add some indicators
        """
        x = 5
        data = MA(data, x)
        data = MOM(data, x)
        data = BBANDS(data, x)
        data = RSI(data, x)
        data = EMA(data, x)
        data = ROC(data, x)quant
        data = ATR(data, x)
        data = STO(data, x)
        data = TRIX(data, x)
        data = Vortex(data, x)
        data = ACCDIST(data, x)
        data = MFI(data, x)
        data = OBV(data, x)

        # static
        data = ULTOSC(data)
        data = STOK(data)
        data = Chaikin(data)
        data = PPSR(data)
        data = MassI(data)
        data = MACD(data, 12, 26)
        """

        print data
        data = self.create_lagged_series(data)
        data['Trend'] = data.apply(bucket_return, axis=1, args=['Return'])
        print data
        # data['previous_return_1'] = np.log(data['Close'].shift(-2) / data['Close'].shift(-1)) * 100
        # data['previous_return_2'] = np.log(data['Close'].shift(-3) / data['Close'].shift(-2)) * 100
        # data['previous_return_3'] = np.log(data['Close'].shift(-4) / data['Close'].shift(-3)) * 100
        # data['previous_return_4'] = np.log(data['Close'].shift(-5) / data['Close'].shift(-4)) * 100

        data.fillna(0, inplace=True)
        col_to_drop = []
        for col in data.columns:
            if "Unnamed" in col:
                col_to_drop.append(col)
        data.drop(col_to_drop, axis=1, inplace=True)

        # Now list all columns
        cols = data.columns
        cols_to_use = []
        for col in cols:
            if col in ['Trend', 'Return', 'Open', 'Close', 'High', 'Low']:
                continue
            cols_to_use.append(col)
        for x in range(6):
            pool = itertools.combinations(cols_to_use, x)
            for z in pool:
                # X as predictor values, with Y as the response
                print "Trying %s" % str(list(z))
                X = data[list(z)]
                y = data["Return"]

                # Create training and test sets
                x_split = np.array_split(X, 2)
                y_split = np.array_split(y, 2)
                x_train = x_split[0]
                x_test = x_split[1]
                y_train = y_split[0]
                y_test = y_split[1]

                brain = Brain(x_train, x_test, y_train, y_test)

                brain.perform_regression_analysis()

                y = data["Trend"]
                # Create classification Y training and test sets
                y_split = np.array_split(y, 2)
                y_train = y_split[0]
                y_test = y_split[1]
                brain.y_train = y_train
                brain.y_test = y_test

                brain.perform_classification_analysis()

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
        hit_rate = model.score(X_test, self.y_test)

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
        models = linear
        for m in models:
            try:
                self.fit_model(m.__name__, m(), self.x_train, self.y_train, self.x_test, pred)
            except ValueError:
                print "Not able to do %s" % str(m)


    def perform_classification_analysis(self):
        """
        Performs a number of different classification techniques to try to predict
        value
        """
        # Create prediction DataFrame
        pred = pd.DataFrame(index=self.y_test.index)
        pred["Actual"] = self.y_test

        # Create and fit the three models
        models = classification
        for m in models:
            try:
                self.fit_model(m.__name__, m(), self.x_train, self.y_train, self.x_test, pred)
            except ValueError:
                print "Not able to do %s" % str(m)



linear = [
    LassoLars,
    LassoLarsCV,
    LassoLarsIC,
    LinearRegression,
    Ridge,
    RidgeCV,
    SGDRegressor,
    TheilSenRegressor,
]

classification = [LogisticRegression,
                  LDA,
                  QDA]
