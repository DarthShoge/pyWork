from enum import Enum


class InitError(Exception): pass


class Direction(Enum):
    Short = -1
    Long = 1


class TradeInstruction:
    def __init__(self, price, stop, risk, currency, trade_date):
        self.currency = currency
        self.price = price
        self.stop = stop
        self.risk = risk
        self.trade_date = trade_date

    def __repr__(self):
        return 'p=%s, s=%s, r=%s' % (self.price, self.stop, self.risk)