from decimal import Decimal, getcontext, ROUND_HALF_DOWN


class Position(object):
    def __init__(
        self, home_currency, instrument, units, price
    ):
        self.home_currency = home_currency  # TO BE DEVELOPED
        self.instrument = instrument  # Intended traded currency pair
        self.units = units
        self.avg_price = price
        self.curr_price = price

    def update_curr_price(self, price):
        self.curr_price = price

    def calculate_profit(self):
        profit = (self.curr_price - self.avg_price) * self.units
        return profit.quantize(
            Decimal("0.00001"), ROUND_HALF_DOWN
        )   

    def calculate_profit_perc(self):
        return (self.profit_base / self.units * Decimal("100.00")).quantize(
            Decimal("0.00001"), ROUND_HALF_DOWN
        )

    def add_units(self, units, price):
        # Need to average the price
        new_total_units = self.units + units
        new_total_cost = self.avg_price*self.units + price*units
        self.avg_price = new_total_cost/new_total_units
        self.units = new_total_units

    def remove_units(self, units, price):
        dec_units = Decimal(str(units))

        self.units += dec_units
        # Calculate PnL
        pnl = (price - self.avg_price) * dec_units # might need to have a multiplier
        getcontext().rounding = ROUND_HALF_DOWN
        return pnl.quantize(Decimal("0.01"))

    def close_position(self, price):
        # Calculate PnL
        pnl = (price - self.avg_price) * self.units
        getcontext().rounding = ROUND_HALF_DOWN
        return pnl.quantize(Decimal("0.01"))
