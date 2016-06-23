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
        if signal_event.side == 'close_all':
            try:
                ps = self.book.positions[signal_event.instrument]
            except KeyError:
                self.logger.error("Tried to close all positions but couldnt find one")
                return

            if ps.units < 0:
                side = 'buy'
            else:
                side = 'sell'
            units = abs(ps.units)
        else:
            side = signal_event.side
            units = int(round(int(self.trade_units) * signal_event.units_multiplier))
        time = signal_event.time
        instrument = signal_event.instrument
        # Prepare the order
        order = OrderEvent(instrument, units, "market", side)

        # Very important risk checks against the book.
        if self.risk.check_limit(order):
            self.events.put(order)

            self.logger.info("Portfolio Balance: %s" % self.book.balance)
        else:
            self.logger.info("Unable to execute order as breached limit checks.")
