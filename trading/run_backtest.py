from __future__ import print_function

from backtest.backtest import Backtest
from execution.execution import SimulatedExecution
from manager.fill import FillManager
from manager.order import OrderManager
from portfolio.book import Book
import settings
from strategy.gridiron import GridIron

from data.price import HistoricCSVPriceHandler
from strategy.gridlock import GridLock
from strategy.mustang import Mustang

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


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