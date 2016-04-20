from decimal import Decimal, getcontext, ROUND_HALF_DOWN


class Position(object):
    def __init__(
        self, home_currency, instrument, units, price
    ):
        self.home_currency = home_currency  # Account denomination (e.g. GBP)
        self.instrument = instrument  # Intended traded currency pair
        self.units = units
        self.avg_price = price
        self.curr_price = price

    def update_curr_price(self, price):
        self.curr_price = price

    def calculate_profit(self):
        pips = self.calculate_pips()
        ticker_qh = self.ticker.prices[self.quote_home_currency_pair]
        if self.position_type == "long":
            qh_close = ticker_qh["bid"]
        else:
            qh_close = ticker_qh["ask"]
        profit = pips * qh_close * self.units
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

        self.units -= dec_units
        # Calculate PnL
        pnl = self.calculate_pips() * price * dec_units
        getcontext().rounding = ROUND_HALF_DOWN
        return pnl.quantize(Decimal("0.01"))

    def close_position(self, price):
        ticker_cp = self.ticker.prices[self.currency_pair]
        ticker_qh = self.ticker.prices[self.quote_home_currency_pair]
        if self.position_type == "long":
            qh_close = ticker_qh["ask"]
        else:
            qh_close = ticker_qh["bid"]
        self.update_position_price()
        # Calculate PnL
        pnl = self.calculate_pips() * qh_close * self.units
        getcontext().rounding = ROUND_HALF_DOWN
        return pnl.quantize(Decimal("0.01"))
