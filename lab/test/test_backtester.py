import unittest
from unittest.mock import MagicMock
import pandas as pd
import lab.test.helpers
from typing import List
from lab.core.position import Position
from lab.core.common import get_range, get_pips, as_price
from lab.core.structures import TradeInstruction
from lab.data.dataprovider import DataProvider
from lab.strategy.strategy import Strategy


class BacktesterTests(unittest.TestCase):

    def create_fake_dataprovider(self, data):
        dp = DataProvider()
        dp.get_rates = MagicMock(return_value=data)
        return dp

    def create_fake_strategy(self):
        strtgy = Strategy

    def test_backtester_is_given_no_dataprovider_then_empty_attribution_is_returned(self):
        fake_dp = self.create_fake_dataprovider(pd.DataFrame)

        backtester = Backtester2(fake_dp)
        results = backtester.backtest(10000)


class Backtester2:
    def __init__(self, dp: DataProvider, strategy: Strategy):
        self.dataprovider = dp
        self.strategy = strategy
        self.position_pnls = []

    def backtest(self, capital):
        return []

class SimpleMovingAvgStrategy(Strategy):

    def __init__(self, lookback=3,stop_value = 200):
        self.stop_value = stop_value
        self.lookback = lookback

    def schedule(self, positions: List[Position], data_ser: pd.Series):
        avg: pd.Series = data_ser.rolling(self.lookback).mean()
        has_pos = positions != []
        todays_price_ = data_ser[-1]
        if data_ser[-2] < avg[-2] and todays_price_ > avg[-1]:
            tran = TradeInstruction(todays_price_, todays_price_ - as_price(self.stop_value))

    def run(self, rates):
        pass