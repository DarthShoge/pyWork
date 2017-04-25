import unittest
from unittest.mock import MagicMock
import pandas as pd
import lab.test.helpers as hp
from typing import List
from lab.core.position import Position
from lab.core.common import get_range, get_pips, as_price
from lab.core.structures import TradeInstruction, BacktestContext
from lab.core.transaction import Transaction
from lab.data.dataprovider import DataProvider
from lab.strategy.strategy import Strategy


def create_ohcl_series():
    data = [hp.ohcl(1, 0.9980, 1.0010, 0.9979),
            hp.ohcl(0.9980, 0.9962, 0.9994, 0.9950),
            hp.ohcl(0.9952, 0.9970, 0.9982, 0.9948),
            hp.ohcl(0.9970, 1.0060, 1.0061, 0.9948),
            hp.ohcl(1.0080, 1.018, 1.1093, 1.0001)]
    return hp.ohlc_series(data)


class BacktesterTests(unittest.TestCase):
    def create_fake_dataprovider(self, data):
        dp = DataProvider()
        dp.get_rates = MagicMock(return_value=data)
        return dp

    def test_when_strategy_places_trade_with_no_transaction_costs_then_transactions_not_included_in_attribution(self):
        gbpusd = hp.ohlc_series([hp.ohcl(1, 0.9980, 1.0010, 0.9979),
            hp.ohcl(0.9980, 0.9962, 0.9994, 0.9950),
            hp.ohcl(0.9952, 0.9970, 0.9982, 0.9948),
            hp.ohcl(0.9970, 1.0060, 1.0061, 0.9948),
            hp.ohcl(1.0080, 1.018, 1.1093, 1.0001)],'GBPUSD')
        fake_dp = self.create_fake_dataprovider(pd.DataFrame(gbpusd))
        strtgy = SimpleMovingAvgStrategy()

        backtester = Backtester2(fake_dp, strtgy)
        results = backtester.backtest(10000)
        expected = list(map(lambda x: 10000, range(len(gbpusd))))
        self.assertEquals(expected,results.attribution['gbpusd '])

    def test_backtester_is_given_no_dataprovider_then_empty_attribution_is_returned(self):
        fake_dp = self.create_fake_dataprovider(pd.DataFrame())
        strtgy = SimpleMovingAvgStrategy()

        backtester = Backtester2(fake_dp, strtgy)
        results = backtester.backtest(10000)
        self.assertTrue(results.attribution.empty)


class Backtester2:
    def __init__(self, dp: DataProvider, strategy: Strategy):
        self.dataprovider = dp
        self.strategy = strategy
        self.position_pnls = []

    def backtest(self, capital):
        self.context = BacktestContext(capital)
        return BacktestResults()


class BacktestResults:
    def __init__(self):
        self.attribution: pd.DataFrame = pd.DataFrame()
        self.headlinePnL = 0


class SimpleMovingAvgStrategy(Strategy):
    def __init__(self, lookback=2, stop_value=200):
        self.stop_value = stop_value
        self.lookback = lookback
        self.risk_per_trade = 0.01

    def schedule(self, positions: List[Position], data_ser: pd.Series, context: BacktestContext):
        avg: pd.Series = data_ser.apply(lambda x: x.open).rolling(self.lookback).mean()
        has_pos = context.positions != []
        todays_price_ = data_ser[-1].open
        if data_ser[-2].open <= avg[-2] and todays_price_ > avg[-1]:
            instruction = TradeInstruction(todays_price_, todays_price_ - as_price(self.stop_value),
                                           self.risk_per_trade,
                                           data_ser.name, data_ser[-1].trade_date)
            if has_pos:
                pos = context.positions[-1]
                context.capital = pos.revalue_position(instruction, data_ser[-1], context.capital)
            else:
                context.positions.append(Position(instruction, context.capital))

        if data_ser[-2].open >= avg[-2] and todays_price_ < avg[-1]:
            instruction = TradeInstruction(todays_price_, todays_price_ + as_price(self.stop_value),
                                           self.risk_per_trade,
                                           data_ser.name, data_ser[-1].trade_date)
            if has_pos:
                pos = context.positions[-1]
                context.capital = pos.revalue_position(instruction, data_ser[-1], context.capital)
            else:
                context.positions.append(Position(instruction, context.capital))

        return context

    def run(self, rates):
        pass
