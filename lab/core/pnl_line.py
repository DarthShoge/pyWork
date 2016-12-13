import time
import numpy as np
from lab.core.structures import TradeInstruction
from enum import Enum


class ExitType(Enum):
    Stopped = 0
    Closed = 1
    Multi = 2


class PnlLine:
    def __init__(self, opening_trade, to_date=None, close_price=np.NaN, pnl=0):
        self.__openingtrade__ = opening_trade
        self.to_date = to_date
        self.from_date = opening_trade.trade_date
        self.currency = opening_trade.currency
        self.open_price = opening_trade.price
        self.close_price = close_price
        self.exit_type = ExitType.Closed
        self.pnl = pnl

    def __add__(self, other):
        if self.currency != other.currency:
            raise LookupError("Currencies do not match")

        from_date = self.from_date if self.from_date < other.to_date else other.from_date
        to_date = self.to_date if self.to_date > other.to_date else other.to_date
        open_price = self.open_price if self.from_date < other.from_date else other.open_price
        closing_price = self.close_price if self.to_date > other.to_date else other.close_price
        pnl_line = PnlLine(self.__openingtrade__, pnl=self.pnl + other.pnl, to_date=to_date,close_price=closing_price)
        pnl_line.from_date = from_date
        pnl_line.open_price = open_price
        pnl_line.exit_type = ExitType.Multi if self.exit_type is not other.exit_type else self.exit_type
        return pnl_line

    @staticmethod
    def sum(lines):

        if not lines:
            return None

        acca = lines[0]
        for l in lines[1:]:
            acca = acca + l
        return acca

