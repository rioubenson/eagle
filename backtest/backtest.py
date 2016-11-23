from __future__ import print_function

#from statistics.statistics import Statistics
from datetime import datetime

from data.price import BarGenerator
from statistics.statistics import Statistics

try:
    import Queue as queue
except ImportError:
    import queue
import time

import settings


class Backtest(object):
    """
    Enscapsulates the settings and components for carrying out
    an event-driven backtest on the foreign exchange markets.
    """
    def __init__(
        self, pairs, data_handler, strategy, 
        book, order, execution, fill,
        equity=100000.0, heartbeat=0.0001,
        max_iters=10000000000
    ):
        """
        Initialises the backtest.
        """
        self.pairs = pairs
        self.events = queue.Queue()
        self.csv_dir = settings.CSV_DATA_DIR
        self.ticker = data_handler(self.pairs, self.events, self.csv_dir)
        #self.strategy_params = strategy_params
        self.equity = equity
        self.heartbeat = heartbeat
        self.max_iters = max_iters
        self.book = book(
            self.ticker, self.events, equity=self.equity, backtest=True
        )
        self.order = order(self.events, self.book)
        self.fill = fill(self.events, self.book)
        self.execution = execution()
        self.strategy = strategy(
            self.pairs, self.events  # , **self.strategy_params
        )

    def _run_backtest(self):
        """
        Carries out an infinite while loop that polls the 
        events queue and directs each event to either the
        strategy component of the execution handler. The
        loop will then pause for "heartbeat" seconds and
        continue unti the maximum number of iterations is
        exceeded.
        """
        print("Running Backtest...")
        iters = 0
        # set up the bar generator
        bar_generator = BarGenerator()
        while iters < self.max_iters and self.ticker.continue_backtest:
            try:
                event = self.events.get(False)
            except queue.Empty:
                self.ticker.stream_next_tick()
            else:
                if event is not None:
                    if event.type == 'TICK':
                        # Create bars
                        bar = bar_generator.add_tick(event)
                        if not bar == None:
                            self.events.put(bar)
                        self.strategy.calculate_signals(event)
                        self.book.update_book(event)
                        self.execution.mock_market_price(event)
                    elif event.type == 'BAR':
                        self.strategy.new_bar(event)
                    elif event.type == 'SIGNAL':
                        self.order.execute_signal(event)
                    elif event.type == 'ORDER':
                        fill_event = self.execution.execute_order(event)
                        self.events.put(fill_event) # mock a fill
                    elif event.type == 'FILL':
                        self.fill.execute_fill(event)
            time.sleep(self.heartbeat)
            iters += 1

    def _output_performance(self):
        """
        Outputs the strategy performance from the backtest.
        """
        print("Calculating Performance Metrics...")
        #self.book.output_results()

    def simulate_trading(self):
        """
        Simulates the backtest and outputs portfolio performance.
        """
        self._run_backtest()
        self._output_performance()
        print("Backtest complete.")
        #statistics = Statistics()
        #statistics.generate_results()
        #statistics.plot_results()
