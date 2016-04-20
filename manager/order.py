import logging

from event.event import OrderEvent
from manager.risk import RiskManager


class OrderManager(object):

    def __init__(
            self, events, book
    ):
        self.events = events
        self.book = book
        self.logger = logging.getLogger(__name__)
        self.risk = RiskManager(book)
        self.trade_units = book.trade_units

    def execute_signal(self, signal_event):
        # Check that the prices ticker contains all necessary
        # currency pairs prior to executing an manager
        self.logger.info("Received Signal, %s" % str(signal_event))

        # All necessary pricing data is available,
        # we can try to execute
        side = signal_event.side
        instrument = signal_event.instrument
        multi = 1 if side == 'buy' else -1
        order_units = int(self.trade_units)
        positions_units = order_units * multi # means negative for short
        time = signal_event.time

        # Prepare the order
        order = OrderEvent(instrument, order_units, "market", side)

        # Very important risk checks against the book.
        if self.risk.check_limit(order):
            self.events.put(order)

            self.logger.info("Portfolio Balance: %s" % self.balance)
        else:
            self.logger.info("Unable to execute order as breached limit checks.")
