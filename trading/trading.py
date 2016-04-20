import copy
from decimal import Decimal, getcontext
import logging
import logging.config

from dropcopy.dropcopy import OANDAStreamingDropcopy
from manager.order import OrderManager
from manager.fill import FillManager

try:
    import Queue as queue
except ImportError:
    import queue
import threading
import time

from execution.execution import OANDAExecutionHandler
from portfolio.book import Portfolio
import settings
from strategy.gridiron import GridIron
from data.streaming import StreamingForexPrices


def trade(events, strategy, portfolio, order, execution, fill, heartbeat):
    """
    Carries out an infinite while loop that polls the
    events queue and directs each event to either the
    strategy component of the execution handler. The
    loop will then pause for "heartbeat" seconds and
    continue.
    """
    while True:
        try:
            event = events.get(False)
        except queue.Empty:
            pass
        else:
            if event is not None:
                if event.type == 'TICK':
                    logger.info("Received new tick event: %s", event)
                    strategy.calculate_signals(event)
                    portfolio.update_portfolio(event)
                elif event.type == 'SIGNAL':
                    logger.info("Received new signal event: %s", event)
                    order.execute_signal(event)
                elif event.type == 'ORDER':
                    logger.info("Received new manager event: %s", event)
                    execution.execute_order(event)
                elif event.type == 'FILL':
                    logger.info("Received new manager event: %s", event)
                    fill.execute_fill(event)
        time.sleep(heartbeat)


if __name__ == "__main__":
    # Set up logging
    logging.config.fileConfig('../logging.conf')
    logger = logging.getLogger('eagle.trading.trading')

    # Set the number of decimal places to 2
    getcontext().prec = 2

    heartbeat = 0.0  # Time in seconds between polling
    events = queue.Queue()
    equity = settings.EQUITY

    # Pairs to include in streaming data set
    pairs = ["EURUSD"]

    # Create the OANDA market price streaming class
    # making sure to provide authentication commands
    prices = StreamingForexPrices(
        settings.STREAM_DOMAIN, settings.ACCESS_TOKEN,
        settings.ACCOUNT_ID, pairs, events
    )

    # Create the OANDA dropcopy streaming class
    # making sure to provide authentication commands
    dropcopy = OANDAStreamingDropcopy(
        settings.STREAM_DOMAIN, settings.ACCESS_TOKEN,
        settings.ACCOUNT_ID, pairs, events
    )

    # Create the strategy/signal generator, passing the
    # instrument and the events queue
    strategy = GridIron(pairs, events)

    # Create the portfolio object that will be used to
    # compare the OANDA positions with the local, to
    # ensure backtesting integrity.
    portfolio = Portfolio(
        prices, events, equity=equity, backtest=False
    )

    # Create an order manager
    order = OrderManager(events, portfolio)

    # Create an fill manager
    fill = FillManager(events, portfolio)

    # Create the execution handler making sure to
    # provide authentication commands
    execution = OANDAExecutionHandler(
        settings.API_DOMAIN,
        settings.ACCESS_TOKEN,
        settings.ACCOUNT_ID
    )

    # Create two separate threads: One for the trading loop
    # and another for the market price streaming class
    trade_thread = threading.Thread(
        target=trade, args=(
            events, strategy, portfolio, order, execution, fill, heartbeat
        )
    )
    price_thread = threading.Thread(target=prices.stream_to_queue, args=[])

    dropcopy_thread = threading.Thread(target=dropcopy.stream_to_queue, args=[])

    # Start all threads
    logger.info("Starting trading thread")
    trade_thread.start()
    logger.info("Starting price streaming thread")
    price_thread.start()
    logger.info("Starting dropcopy streaming thread")
    dropcopy_thread.start()