import unittest
from typing import List
from unittest.mock import MagicMock

import numpy as np
import pandas as pd

import lab.test.helpers as hp
from lab.core.backtester import Backtester2
from lab.core.common import as_price
from lab.core.position import Position
from lab.core.structures import TradeInstruction, BacktestContext
from lab.data.dataprovider import DataProvider
from lab.strategy.strategy import Strategy


def create_ohcl_series():
    data = [hp.ohcl(1, 0.9980, 1.0010, 0.9979),
            hp.ohcl(0.9980, 0.9962, 0.9994, 0.9950),
            hp.ohcl(0.9952, 0.9970, 0.9982, 0.9948),
            hp.ohcl(0.9970, 1.0060, 1.0061, 0.9948),
            hp.ohcl(1.0080, 1.018, 1.1093, 1.0001)]
    return hp.ohlc_series(data)

def create_dataframe_from_series(data : List[pd.Series]):
    return pd.concat(data, axis=1, keys=[s.name for s in data])

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
        strtgy = SimpleMovingAvgStrategy()

        backtester = Backtester2(strtgy)
        results = backtester.backtest(10000,price_data=create_dataframe_from_series([gbpusd]))
        expected = [0,0,0,0]
        actual = results.nominal_attribution['GBPUSD'].values
        self.assertEquals(set(expected),set(actual))

    def test_when_strategy_places_trade_with_transaction_costs_then_transactions_included_in_attribution(self):
        gbpusd = hp.ohlc_series([hp.ohcl(1, 0.9980, 1.0010, 0.9979),
            hp.ohcl(0.9980, 0.9962, 0.9994, 0.9950),
            hp.ohcl(0.9952, 0.9970, 0.9982, 0.9948),
            hp.ohcl(0.9970, 1.0060, 1.0061, 0.9948),
            hp.ohcl(1.0080, 1.018, 1.1093, 1.0001)],'GBPUSD')
        strtgy = SimpleMovingAvgStrategy()

        backtester = Backtester2(strtgy)
        results = backtester.backtest(10000,price_data=create_dataframe_from_series([gbpusd]),commission_per_k=0.5)
        expected = [0,0,-5,0]
        actual = results.nominal_attribution['GBPUSD'].values
        self.assertEquals(list(expected),list(actual))

    def test_backtester_is_given_no_dataprovider_then_empty_attribution_is_returned(self):
        strtgy = SimpleMovingAvgStrategy()

        backtester = Backtester2(strtgy)
        results = backtester.backtest(10000,price_data = pd.DataFrame())
        self.assertTrue(results.nominal_attribution.empty)

    def test_when_strategy_places_trade_and_exits_trade_pnl_is_captured_in_attribution(self):
        gbpusd = self.create_traded_series()
        strtgy = SimpleMovingAvgStrategy()

        backtester = Backtester2(strtgy)
        results = backtester.backtest(10000,price_data=create_dataframe_from_series([gbpusd]),commission_per_k=0.5)
        expected = [0,0,-5,0,28.5,0]
        actual = results.nominal_attribution['GBPUSD'].values
        np.testing.assert_almost_equal(list(expected),list(actual),decimal=3)

    def test_when_strategy_places_trade_and_exits_then_pct_attribution_is_correctly_calculated(self):
        gbpusd = self.create_traded_series()
        strtgy = SimpleMovingAvgStrategy()

        backtester = Backtester2(strtgy)
        results = backtester.backtest(10000,price_data=create_dataframe_from_series([gbpusd]),commission_per_k=0.5)
        expected = [0,0,0,0,0.00570,0]
        actual = results.attribution['GBPUSD'].values
        np.testing.assert_almost_equal(list(expected),list(actual),decimal=3)

    def test_when_strategy_places_trade_and_exits_trade_pnl_is_captured_in_attribution(self):
        gbpusd = self.create_traded_series()
        strtgy = SimpleMovingAvgStrategy()

        backtester = Backtester2(strtgy)
        results = backtester.backtest(10000,price_data=create_dataframe_from_series([gbpusd]),commission_per_k=0.5)
        expected = [0,0,-5,0,28.5,0]
        actual = results.nominal_attribution['GBPUSD'].values
        np.testing.assert_almost_equal(list(expected),list(actual),decimal=3)


    def test_when_strategy_places_trade_and_exits_trade_for_multiple_currencies_pnl_is_captured_in_attribution(self):
        gbpusd = self.create_traded_series()
        strtgy = SimpleMovingAvgStrategy()

        backtester = Backtester2(strtgy)
        results = backtester.backtest(10000,price_data=create_dataframe_from_series([gbpusd]),commission_per_k=0.5)
        expected = [0,0,-5,0,28.5,0]
        actual = results.nominal_attribution['GBPUSD'].values
        np.testing.assert_almost_equal(list(expected),list(actual),decimal=3)


    def test_when_strategy_places_trade_and_exits_trade_for_multiple_currencies_pnl_is_captured_in_attribution(self):
        gbpusd = self.create_traded_series('GBPUSD')
        eurusd = self.create_traded_series('EURUSD')
        strtgy = SimpleMovingAvgStrategy()

        backtester = Backtester2(strtgy)
        results = backtester.backtest(10000,price_data=create_dataframe_from_series([gbpusd,eurusd]),commission_per_k=0.5)
        expected = [0,0,-10,0,57,0]
        actual = results.nominal_attribution.apply(sum, axis=1).values
        np.testing.assert_almost_equal(list(expected),list(actual),decimal=3)


    def create_traded_series(self, currency='GBPUSD'):
        ser = hp.ohlc_series([hp.ohcl(1, 0.9980, 1.0010, 0.9979),
                                 hp.ohcl(0.9980, 0.9962, 0.9994, 0.9950),
                                 hp.ohcl(0.9952, 0.9970, 0.9982, 0.9948),
                                 hp.ohcl(0.9970, 1.0060, 1.0061, 0.9948),  # Enter the trade at this point
                                 hp.ohcl(1.0080, 1.0095, 1.0027, 1.0001),
                                 hp.ohcl(1.0027, 1.018, 0.9975, 1.0003),  # Exit the trade at this point
                                 hp.ohcl(0.9975, 1.0003, 0.9920, 0.9920), ], currency)
        return ser


class SimpleMovingAvgStrategy(Strategy):
    def __init__(self, lookback=2, stop_value=200):
        self.stop_value = stop_value
        self.lookback = lookback
        self.risk_per_trade = 0.01

    def schedule(self, positions: List[Position], data_ser: pd.Series, context: BacktestContext):
        avg: pd.Series = data_ser.apply(lambda x: x.open).rolling(self.lookback).mean()
        todays_price_ = data_ser[-1].open
        instruction = None
        if data_ser[-2].open <= avg[-2] and todays_price_ > avg[-1]:
            instruction = TradeInstruction(todays_price_, todays_price_ - as_price(self.stop_value, data_ser.name),
                                           self.risk_per_trade,
                                           data_ser.name, data_ser.index[-1])


        if data_ser[-2].open >= avg[-2] and todays_price_ < avg[-1]:
            instruction = TradeInstruction(todays_price_, todays_price_ + as_price(self.stop_value, data_ser.name),
                                           -self.risk_per_trade,
                                           data_ser.name, data_ser.index[-1])

        return instruction

    def run(self, rates):
        pass
