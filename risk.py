import logging

from portfolio.book import TRADE, RESTRICTED


class RiskManager(object):
    def __init__(
            self, book
    ):
        self.book = book
        self.logger = logging.getLogger(__name__)

    def check_limit(self, order):

        multi = -1 if order.side == 'sell' else 1
        real_units = int(order.units) * multi

        # Check book is set to tradable
        if self.book.trade_status != TRADE:
            # TODO add logic regarding restricted - check if risk reducing
            self.logger.info("Book is not set to tradable, %s" % self.book.trade_status)
            return False

        # If we are closing positions, allow
        if order.side == 'close_all':
            return True

        # Order size
        if abs(order.units) > self.book.limits['order_size']:
            self.logger.info("Order Size Limit Breached, limit %s, attempted %s" % (order.units,
                                                                                    self.book.limits['order_size']))
            return False

        # Position check
        current_position = self.book.positions.get(order.instrument, None)
        if current_position is not None and abs(current_position.units + real_units) > self.book.limits['position_size']:
            self.logger.info(
                "Position Size Limit Breached, limit %s, attempted %s" % (current_position.units, self.book.limits['position_size']))
            return False

        # TODO MinMax check - for passive orders

        # PnL
        if self.book.realised_pnl < self.book.limits['pnl_limit']:
            self.logger.info(
                "PnL Limit Breached, limit %s, attempted %s" % (order.units,
                                                                self.book.limits['pnl_limit']))
            return False
        return True
