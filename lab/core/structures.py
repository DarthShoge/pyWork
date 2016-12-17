from enum import Enum


class InitError(Exception): pass


class Direction(Enum):
    Short = -1
    Long = 1


class Ohlc:
    def __init__(self, open, high, low, close, volume=0):
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume

    def __repr__(self):
        return "o:%s h:%s l:%s c:%s" % (self.open, self.high, self.low, self.close)


class TradeInstruction:
    def __init__(self, price, stop, risk, currency, trade_date):
        self.currency = currency
        self.price = price
        self.stop = stop
        self.risk = risk
        self.trade_date = trade_date

    def __repr__(self):
        return 'p=%s, s=%s, r=%s' % (self.price, self.stop, self.risk)
