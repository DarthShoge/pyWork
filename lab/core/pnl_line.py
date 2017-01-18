import time
import numpy as np
from lab.core.structures import TradeInstruction
from enum import Enum


class ExitType(Enum):
    Stopped = 0
    Closed = 1
    Multi = 2


class PnlLine:
    def __init__(self, opening_trade, initial_capital=np.NaN, to_date=None, close_price=np.NaN, pnl=0, details=[]):
        self.__openingtrade__ = opening_trade
        self.details = [opening_trade] if not details else details
        self.to_date = to_date
        self.from_date = opening_trade.trade_date
        self.currency = opening_trade.currency
        self.initial_capital = initial_capital
        self.open_price = opening_trade.price
        self.close_price = close_price
        self.exit_type = ExitType.Closed
        self.returns = np.NaN
        self.__pnl__ = pnl
        if pnl != 0 and initial_capital != 0:
            self.returns = self.returns if initial_capital is np.NaN else pnl / initial_capital

    @property
    def pnl(self):
        return self.__pnl__

    @pnl.setter
    def pnl(self, value):
        self.__pnl__ = value
        if value != 0 and self.initial_capital != 0:
            self.returns = np.NaN if self.initial_capital is np.NaN else value / self.initial_capital

    def __add__(self, other):
        if self.currency != other.currency:
            raise LookupError("Currencies do not match")

        from_date = self.from_date if self.from_date < other.to_date else other.from_date
        to_date = self.to_date if self.to_date > other.to_date else other.to_date
        open_price = self.open_price if self.from_date < other.from_date else other.open_price
        initial_cap = self.initial_capital if self.from_date < other.to_date and not np.isnan(
            self.initial_capital) else other.initial_capital
        closing_price = self.close_price if self.to_date > other.to_date else other.close_price
        pnl_line = PnlLine(self.__openingtrade__, pnl=self.pnl + other.pnl, to_date=to_date, close_price=closing_price,
                           initial_capital=initial_cap, details=self.details + other.details)

        pnl_line.from_date = from_date
        pnl_line.open_price = open_price
        pnl_line.exit_type = ExitType.Multi if self.exit_type is not other.exit_type else self.exit_type
        return pnl_line

    def __repr__(self):
        return "pnl: %d ret: %f from:%s to:%s" % (self.pnl, self.returns, self.from_date, self.to_date)

    @staticmethod
    def sum(lines):

        if not lines:
            return None

        acca = lines[0]
        for l in lines[1:]:
            acca = acca + l
        return acca
