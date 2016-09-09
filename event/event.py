class Event(object):
    pass


class TickEvent(Event):
    def __init__(self, instrument, time, bid, ask):
        self.type = 'TICK'
        self.instrument = instrument
        self.time = time
        self.bid = bid
        self.ask = ask
        self.mid = (bid + ask) / 2

    def __str__(self):
        return "Type: %s, Instrument: %s, Time: %s, Bid: %s, Ask: %s" % (
            str(self.type), str(self.instrument), 
            str(self.time), str(self.bid), str(self.ask)
        )

    def __repr__(self):
        return str(self)


class BarEvent(Event):
    def __init__(self, instrument, time, interval, open_mid,  close_mid, high_mid, low_mid, volume):
        self.type = 'BAR'
        self.time = time
        self.instrument = instrument
        self.interval = interval
        self.open = open_mid
        self.close = close_mid
        self.high = high_mid
        self.low = low_mid
        self.volume = volume

    def __str__(self):
        return "Type: %s, Instrument: %s, Interval: %s, Time: %s, Open: %s, Close: %s, High: %s, Low: %s, Vol: %s" % (
            str(self.type), str(self.instrument),
            str(self.time), str(self.interval), str(self.open), str(self.close), str(self.high), str(self.low),
            str(self.volume)
        )

    def __repr__(self):
        return str(self)


class SignalEvent(Event):
    def __init__(self, instrument, order_type, side, time, units_multiplier=1):
        self.type = 'SIGNAL'
        self.instrument = instrument
        self.order_type = order_type
        self.side = side
        self.units_multiplier = units_multiplier
        self.time = time  # Time of the last tick that generated the signal

    def __str__(self):
        return "Type: %s, Instrument: %s, Order Type: %s, Side: %s" % (
            str(self.type), str(self.instrument), 
            str(self.order_type), str(self.side)
        )

    def __repr__(self):
        return str(self)


class OrderEvent(Event):
    def __init__(self, instrument, units, order_type, side):
        self.type = 'ORDER'
        self.instrument = instrument
        self.units = units
        self.order_type = order_type
        self.side = side

    def __str__(self):
        return "Type: %s, Instrument: %s, Units: %s, Order Type: %s, Side: %s" % (
            str(self.type), str(self.instrument), str(self.units),
            str(self.order_type), str(self.side)
        )

    def __repr__(self):
        return str(self)


class FillEvent(Event):
    """
    Encapsulates the notion of a filled order, as returned
    from a brokerage. Stores the quantity of an instrument
    actually filled and at what price. In addition, stores
    the commission of the trade from the brokerage.

    TODO: Currently does not support filling positions at
    different prices. This will be simulated by averaging
    the cost.
    """

    def __init__(
        self, timestamp, instrument,
        side, units,
        exchange, price,
        commission
    ):
        """
        Initialises the FillEvent object.
        timestamp - The timestamp when the order was filled.
        insturment - The ticker symbol, e.g. 'GOOG', EURUSD etc
        side - 'buy' or 'sell'.
        units - The filled quantity.
        exchange - The exchange where the order was filled.
        price - The price at which the trade was filled
        commission - The brokerage commission for carrying out the trade.
        """
        self.type = 'FILL'
        self.timestamp = timestamp
        self.instrument = instrument
        self.side = side
        self.units = units
        self.exchange = exchange
        self.price = price
        self.commission = commission

    def __str__(self):
        return "Type: %s, Instrument: %s, Units: %s, Price: %s, Side: %s" % (
            str(self.type), str(self.instrument), str(self.units),
            str(self.price), str(self.side)
        )

    def __repr__(self):
        return str(self)
