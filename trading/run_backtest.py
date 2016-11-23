from __future__ import print_function

import logging.config

import warnings

import settings
from backtest.backtest import Backtest
from data.price import HistoricCSVPriceHandler
from execution.execution import SimulatedExecution
from fill import FillManager
from order import OrderManager
from portfolio.book import Book
from strategy.gridiron import GridIron
from strategy.gridlock import GridLock

warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.config.fileConfig('../logging.conf')
logger = logging.getLogger('eagle.trading.trading')

if __name__ == "__main__":
    # Trade on GBP/USD and EUR/USD
    pairs = ["EURUSD"]

    # Create and execute the backtest
    backtest = Backtest(
        pairs, HistoricCSVPriceHandler,
        GridIron,
        Book, OrderManager, SimulatedExecution, FillManager,
        equity=settings.EQUITY
    )
    backtest.simulate_trading()