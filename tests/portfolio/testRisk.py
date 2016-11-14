import unittest

from event import OrderEvent

try:
    import Queue as queue
except ImportError:
    import queue
from portfolio.book import Book, STOP, FLATTEN
from risk import RiskManager


class TestRiskManager(unittest.TestCase):

    limits = {'order_size': 100,
              'order_value': 1000,
              'position_size': 5000,
              'pnl_limit': -10000
              }

    def test_trading_status(self):

        # create a book
        book = Book("EURUSD")
        book.limits = self.limits

        risk = RiskManager(book)

        order = OrderEvent("EURUSD", 10, "market", "buy")

        self.assertTrue(risk.check_limit(order), "Order is restricted incorrectly")

        # Set book to stop
        book.trade_status = STOP
        self.assertFalse(risk.check_limit(order), "Order is has been allowed, WRONG")

        book.trade_status = FLATTEN
        self.assertFalse(risk.check_limit(order), "Order is has been allowed, WRONG")

    def test_order_size(self):
        # create a book
        book = Book("EURUSD")
        book.limits = self.limits

        risk = RiskManager(book)

        order = OrderEvent("EURUSD", 99, "market", "buy")

        self.assertTrue(risk.check_limit(order), "Order is restricted incorrectly")

        # Too large an order
        order = OrderEvent("EURUSD", 101, "market", "buy")
        self.assertFalse(risk.check_limit(order), "Order is has been allowed, WRONG")

    def test_position_size_long(self):
        # create a book
        book = Book("EURUSD")
        book.limits = self.limits

        risk = RiskManager(book)

        order = OrderEvent("EURUSD", 50, "market", "buy")

        self.assertTrue(risk.check_limit(order), "Order is restricted incorrectly")

        # Too many positions
        book.add_new_position("EURUSD", 4999) # Near limit

        order = OrderEvent("EURUSD", 10, "market", "buy")
        self.assertFalse(risk.check_limit(order), "Order is has been allowed, WRONG")

    def test_position_size_short(self):
        # create a book
        book = Book("EURUSD")
        book.limits = self.limits

        risk = RiskManager(book)

        order = OrderEvent("EURUSD", 50, "market", "sell")

        self.assertTrue(risk.check_limit(order), "Order is restricted incorrectly")

        # Too many positions
        book.add_new_position("EURUSD", -4999)  # Near limit

        order = OrderEvent("EURUSD", 10, "market", "sell")
        self.assertFalse(risk.check_limit(order), "Order is has been allowed, WRONG")

    def test_pnl_limit(self):
        # create a book
        book = Book("EURUSD")
        book.limits = self.limits

        risk = RiskManager(book)

        order = OrderEvent("EURUSD", 50, "market", "sell")

        self.assertTrue(risk.check_limit(order), "Order is restricted incorrectly")

        book.pnl = -11000

        self.assertFalse(risk.check_limit(order), "Order is has been allowed, WRONG")

