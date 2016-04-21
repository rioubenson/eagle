from __future__ import print_function

from copy import deepcopy
from decimal import Decimal, getcontext, ROUND_HALF_DOWN
import logging
import os

import pandas as pd

from position import Position
from performance.performance import create_drawdowns
from settings import OUTPUT_RESULTS_DIR

# List of book trading status
TRADE = 'trade' # Full Trading allowed
STOP = 'stop' # End Trading completely
FLATTEN = 'flatten' # Only risk reducing orders allowed
RESTRICTED = 'restricted' # Temp no trading allowed - e.g limit breach


class Book(object):
    def __init__(
        self, ticker, home_currency="GBP",
        leverage=20, equity=Decimal("100000.00"), 
        risk_per_trade=Decimal("0.1"), backtest=False
    ):
        self.ticker = ticker
        self.home_currency = home_currency
        self.leverage = leverage
        self.equity = equity
        self.balance = deepcopy(self.equity)
        self.pnl = 0
        self.risk_per_trade = risk_per_trade
        self.backtest = backtest
        self.trade_units = self.calc_risk_position_size()
        self.positions = {}
        if self.backtest:
            self.backtest_file = self.create_equity_file()
        self.logger = logging.getLogger(__name__)
        self.trade_status = TRADE
        self.limits = self.get_limits_for_book()

    def calc_risk_position_size(self):
        return self.equity * self.risk_per_trade

    def add_new_position(
        self, instrument, units, price,
    ):

        ps = Position(
            self.home_currency,
            instrument, units, price
        )
        self.positions[instrument] = ps

    def adjust_position(self, instrument, units, price):
        if instrument not in self.positions:
            return False
        else:
            ps = self.positions[instrument]

            # if increasing position, then add units
            if units > 0 and ps.units > 0:
                ps.add_units(units, price)
                return True
            elif units < 0 and ps.units < 0:
                ps.add_units(units, price)
                return True
            # If we are long and we have a short (visa versa) remove units
            elif units > 0 > ps.units:
                if abs(units) == abs(ps.units):
                    self.close_position(instrument, price)
                else:
                    pnl = ps.remove_units(units, price)
                    self.balance += pnl
                return True
            elif units < 0 < ps.units:
                if abs(units) == abs(ps.units):
                    self.close_position(instrument, price)
                else:
                    pnl = ps.remove_units(units, price)
                    self.balance += pnl
                return True
            else:
                self.logger.error("Unable to determine how to handle order")
                return False

    def close_position(self, instrument, price):
        if instrument not in self.positions:
            return False
        else:
            ps = self.positions[instrument]
            pnl = ps.close_position(price)
            self.balance += pnl
            print('Closing Position %s' % str(pnl))
            del[self.positions[instrument]]
            return True

    def create_equity_file(self):
        filename = "backtest.csv"
        out_file = open(os.path.join(OUTPUT_RESULTS_DIR, filename), "w")
        header = "Timestamp,Balance"
        for pair in self.ticker.pairs:
            header += ",%s" % pair
        header += "\n"
        out_file.write(header)
        if self.backtest:
            print(header[:-2])
        return out_file

    def output_results(self):
        # Closes off the Backtest.csv file so it can be 
        # read via Pandas without problems
        self.backtest_file.close()
        
        in_filename = "backtest.csv"
        out_filename = "equity.csv" 
        in_file = os.path.join(OUTPUT_RESULTS_DIR, in_filename)
        out_file = os.path.join(OUTPUT_RESULTS_DIR, out_filename)

        # Create equity curve dataframe
        df = pd.read_csv(in_file, index_col=0)
        df.dropna(inplace=True)
        df["Total"] = df.sum(axis=1)
        df["Returns"] = df["Total"].pct_change()
        df["Equity"] = (1.0+df["Returns"]).cumprod()
        
        # Create drawdown statistics
        drawdown, max_dd, dd_duration = create_drawdowns(df["Equity"])
        df["Drawdown"] = drawdown
        df.to_csv(out_file, index=True)
        
        print("Simulation complete and results exported to %s" % out_filename)

    def update_book(self, tick_event):
        """
        This updates all positions ensuring an up to date
        unrealised profit and loss (PnL).
        """
        instrument = tick_event.instrument
        if instrument in self.positions:
            ps = self.positions[instrument]
            ps.update_curr_price(tick_event.mid)
        if self.backtest:
            out_line = "%s,%s" % (tick_event.time, self.balance)
            for pair in self.ticker.pairs:
                if pair in self.positions:
                    out_line += ",%s" % self.positions[pair].calculate_profit()
                else:
                    out_line += ",0.00"
            out_line += "\n"
            print(out_line[:-2])
            self.backtest_file.write(out_line)

    def get_limits_for_book(self):
        return {'order_size': 50000,
                'position_size': 100000,
                'pnl_limit': -10000}