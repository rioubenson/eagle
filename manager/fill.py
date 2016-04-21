import logging

from event.event import OrderEvent
from manager.risk import RiskManager


class FillManager(object):

    def __init__(
            self, events, book
    ):
        self.events = events
        self.book = book
        self.logger = logging.getLogger(__name__)

    def execute_fill(self, fill_event):
        self.logger.info("Received Fill, %s" % str(fill_event))
        instrument = fill_event.instrument
        units = fill_event.units
        side = fill_event.side
        price = fill_event.price
        # If there is no position, create one
        if instrument not in self.book.positions:
            self.book.add_new_position(
                instrument,
                units,
                price
            )

        # If a position exists add or remove units
        else:
            if side == 'sell':
                units = units * -1
                # Close all positions
            self.book.adjust_position(instrument, units, price)

