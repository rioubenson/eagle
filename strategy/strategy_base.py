from abc import abstractmethod, ABCMeta


class Strategy(object):
    """
    Provides an abstract base class to handle all strategies in the
    backtesting and live trading system.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def calculate_signals(self, event):
        """
        The Main method for a given tick
        """
        raise NotImplementedError("Should implement calculate_signals()")

    @abstractmethod
    def new_bar(self, event):
        """
        What to do when a new bar/candle is created
        """
        raise NotImplementedError("Should implement new_bar()")