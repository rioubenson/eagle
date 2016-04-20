import unittest
import time

try:
    import Queue as queue
except ImportError:
    import queue

from event.event import TickEvent
from strategy.gridiron import GridIron


class TestGridIron(unittest.TestCase):
    def test_large_up_trend(self):
        tick = TickEvent("EURUSD", time.time(), 1.1456, 1.1458) # Mock tick event

        events = queue.Queue()
        strategy = GridIron("EURUSD", events)

        strategy.calculate_signals(tick)

        self.assertEqual(strategy.grid.grid_mid, 1.1457, "Grid Mid was not correct")
        self.assertEqual(strategy.grid.buy_level_one, 1.1459, "Grid Buy Level 1 was not correct")
        self.assertEqual(strategy.grid.sell_level_one, 1.1455, "Grid Sell Level 1 was not correct")
        self.assertEqual(strategy.grid.buy_level_two, 1.1461, "Grid Buy Level 2 was not correct")
        self.assertEqual(strategy.grid.sell_level_two, 1.1453, "Grid Sell Level 2 was not correct")
        self.assertEqual(strategy.grid.stop_loss_buy, 1.1455, "Grid Stop Loss was not correct")
        self.assertEqual(strategy.grid.level_triggered, 0, "Unexpected level triggered")

        tick2 = TickEvent("EURUSD", time.time(), 1.1459, 1.1461)

        strategy.calculate_signals(tick2)

        # now check signal
        signal = events.get()
        self.assertEqual(signal.side, "buy", "Buy Signal not generated")
        self.assertEqual(signal.order_type, "market", "Market Signal not generated")

        self.assertEqual(strategy.grid.stop_loss_buy, 1.1457, "Grid Stop Loss was not correct")
        self.assertEqual(strategy.grid.sell_level_one, 1.1455, "Grid Sell Level 1 was not correct")
        self.assertEqual(strategy.grid.buy_level_two, 1.1461, "Grid Buy Level 2 was not correct")
        self.assertEqual(strategy.grid.sell_level_two, 1.1453, "Grid Sell Level 2 was not correct")
        self.assertEqual(strategy.grid.level_triggered, 1, "Unexpected level triggered")

        tick3 = TickEvent("EURUSD", time.time(), 1.1461, 1.1463)

        strategy.calculate_signals(tick3)
        # now check signal
        signal = events.get()
        self.assertEqual(signal.side, "buy", "Buy Signal not generated")
        self.assertEqual(signal.order_type, "market", "Market Signal not generated")

        self.assertEqual(strategy.grid.stop_loss_buy, 1.1459, "Grid Stop Loss was not correct")
        self.assertEqual(strategy.grid.sell_level_one, 1.1455, "Grid Sell Level 1 was not correct")
        self.assertEqual(strategy.grid.sell_level_two, 1.1453, "Grid Sell Level 2 was not correct")
        self.assertEqual(strategy.grid.level_triggered, 2, "Unexpected level triggered")

        tick4 = TickEvent("EURUSD", time.time(), 1.1464, 1.1466)

        strategy.calculate_signals(tick4)
        # now check signal
        signal = events.get()
        self.assertEqual(signal.side, "closeAll", "Close Out Signal not generated")
        self.assertEqual(signal.order_type, "market", "Market Signal not generated")

        self.assertEqual(strategy.grid, None, "Grid not removed")

    def test_large_down_trend(self):
        tick = TickEvent("EURUSD", time.time(), 1.1456, 1.1458)  # Mock tick event

        events = queue.Queue()
        strategy = GridIron("EURUSD", events)

        strategy.calculate_signals(tick)

        self.assertEqual(strategy.grid.grid_mid, 1.1457, "Grid Mid was not correct")
        self.assertEqual(strategy.grid.buy_level_one, 1.1459, "Grid Buy Level 1 was not correct")
        self.assertEqual(strategy.grid.sell_level_one, 1.1455, "Grid Sell Level 1 was not correct")
        self.assertEqual(strategy.grid.buy_level_two, 1.1461, "Grid Buy Level 2 was not correct")
        self.assertEqual(strategy.grid.sell_level_two, 1.1453, "Grid Sell Level 2 was not correct")
        self.assertEqual(strategy.grid.stop_loss_buy, 1.1455, "Grid Stop Loss was not correct")

        tick2 = TickEvent("EURUSD", time.time(), 1.1453, 1.1455)

        strategy.calculate_signals(tick2)

        # now check signal

        signal = events.get()

        self.assertEqual(signal.side, "sell", "Sell Signal not generated")
        self.assertEqual(signal.order_type, "market", "Market Signal not generated")

        self.assertEqual(strategy.grid.stop_loss_sell, 1.1457, "Grid Stop Loss was not correct")
        self.assertEqual(strategy.grid.sell_level_two, 1.1453, "Grid Sell Level 2 was not correct")
        self.assertEqual(strategy.grid.level_triggered, -1, "Unexpected level triggered")

        tick3 = TickEvent("EURUSD", time.time(), 1.1452, 1.1453)

        strategy.calculate_signals(tick3)
        # now check signal
        signal = events.get()
        self.assertEqual(signal.side, "sell", "Sell Signal not generated")
        self.assertEqual(signal.order_type, "market", "Market Signal not generated")

        self.assertEqual(strategy.grid.stop_loss_buy, 1.1455, "Grid Stop Loss was not correct")
        self.assertEqual(strategy.grid.level_triggered, -2, "Unexpected level triggered")

        tick4 = TickEvent("EURUSD", time.time(), 1.1451, 1.1452)

        strategy.calculate_signals(tick4)
        # now check signal
        signal = events.get()
        self.assertEqual(signal.side, "closeAll", "Close Out Signal not generated")
        self.assertEqual(signal.order_type, "market", "Market Signal not generated")

        self.assertEqual(strategy.grid, None, "Grid not removed")

    def test_one_up_then_reversal(self):
        tick = TickEvent("EURUSD", time.time(), 1.1456, 1.1458)  # Mock tick event

        events = queue.Queue()
        strategy = GridIron("EURUSD", events)

        strategy.calculate_signals(tick)

        self.assertEqual(strategy.grid.grid_mid, 1.1457, "Grid Mid was not correct")
        self.assertEqual(strategy.grid.buy_level_one, 1.1459, "Grid Buy Level 1 was not correct")
        self.assertEqual(strategy.grid.sell_level_one, 1.1455, "Grid Sell Level 1 was not correct")
        self.assertEqual(strategy.grid.buy_level_two, 1.1461, "Grid Buy Level 2 was not correct")
        self.assertEqual(strategy.grid.sell_level_two, 1.1453, "Grid Sell Level 2 was not correct")
        self.assertEqual(strategy.grid.stop_loss_buy, 1.1455, "Grid Stop Loss was not correct")

        tick2 = TickEvent("EURUSD", time.time(), 1.1459, 1.1461)

        strategy.calculate_signals(tick2)

        # now check signal
        signal = events.get()
        self.assertEqual(signal.side, "buy", "Buy Signal not generated")
        self.assertEqual(signal.order_type, "market", "Market Signal not generated")

        self.assertEqual(strategy.grid.stop_loss_buy, 1.1457, "Grid Stop Loss was not correct")
        self.assertEqual(strategy.grid.sell_level_one, 1.1455, "Grid Sell Level 1 was not correct")
        self.assertEqual(strategy.grid.buy_level_two, 1.1461, "Grid Buy Level 2 was not correct")
        self.assertEqual(strategy.grid.sell_level_two, 1.1453, "Grid Sell Level 2 was not correct")

        # Now reverse the up move
        tick3 = TickEvent("EURUSD", time.time(), 1.1455, 1.1457)

        strategy.calculate_signals(tick3)
        # now check signal
        signal = events.get()

        self.assertEqual(signal.side, "closeAll", "Close Out Signal not generated")
        self.assertEqual(signal.order_type, "market", "Market Signal not generated")

        self.assertEqual(strategy.grid, None, "Grid not removed")

    def test_one_down_then_reversal(self):
        tick = TickEvent("EURUSD", time.time(), 1.1456, 1.1458)  # Mock tick event

        events = queue.Queue()
        strategy = GridIron("EURUSD", events)

        strategy.calculate_signals(tick)

        self.assertEqual(strategy.grid.grid_mid, 1.1457, "Grid Mid was not correct")
        self.assertEqual(strategy.grid.buy_level_one, 1.1459, "Grid Buy Level 1 was not correct")
        self.assertEqual(strategy.grid.sell_level_one, 1.1455, "Grid Sell Level 1 was not correct")
        self.assertEqual(strategy.grid.buy_level_two, 1.1461, "Grid Buy Level 2 was not correct")
        self.assertEqual(strategy.grid.sell_level_two, 1.1453, "Grid Sell Level 2 was not correct")
        self.assertEqual(strategy.grid.stop_loss_buy, 1.1455, "Grid Stop Loss was not correct")

        tick2 = TickEvent("EURUSD", time.time(), 1.1453, 1.1455)

        strategy.calculate_signals(tick2)

        # now check signal

        signal = events.get()

        self.assertEqual(signal.side, "sell", "Sell Signal not generated")
        self.assertEqual(signal.order_type, "market", "Market Signal not generated")

        self.assertEqual(strategy.grid.stop_loss_sell, 1.1457, "Grid Stop Loss was not correct")
        self.assertEqual(strategy.grid.sell_level_two, 1.1453, "Grid Sell Level 2 was not correct")

        # Now reverse the down move
        tick3 = TickEvent("EURUSD", time.time(), 1.1456, 1.1459)

        strategy.calculate_signals(tick3)
        # now check signal
        signal = events.get()

        self.assertEqual(signal.side, "closeAll", "Close Out Signal not generated")
        self.assertEqual(signal.order_type, "market", "Market Signal not generated")

        self.assertEqual(strategy.grid, None, "Grid not removed")