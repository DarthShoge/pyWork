from enum import Enum


class InitError(Exception): pass


class Direction(Enum):
    Short = -1
    Long = 1

class StopType(Enum):
    Hard = 0
    Soft = 1


class Ohlc:
    def __init__(self,open, high, low, close, date=None, volume=0):
        self.date = date
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume

    def __repr__(self):
        return "o:%s h:%s l:%s c:%s date:%s" % (self.open, self.high, self.low, self.close, self.date)


class TradeInstruction:
    def __init__(self, price, stop, risk, currency, trade_date, stop_type=StopType.Hard):
        self.currency = currency
        self.price = price
        self.stop = stop
        self.stop_type = stop_type
        self.risk = risk
        self.trade_date = trade_date

    def __repr__(self):
        return 'p=%s, s=%s, r=%s' % (self.price, self.stop, self.risk)


class BacktestContext():

    def __init__(self, capital):
        self.commission_per_k = 0.0
        self.spreadmap = []
        self.capital = capital
        self.positions = []