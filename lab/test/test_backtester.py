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
        actual = results.attribution['GBPUSD'].values
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
        expected = [0,0,0,0]
        actual = results.attribution['GBPUSD'].values
        self.assertEquals(set(expected),set(actual))

    def test_backtester_is_given_no_dataprovider_then_empty_attribution_is_returned(self):
        strtgy = SimpleMovingAvgStrategy()

        backtester = Backtester2(strtgy)
        results = backtester.backtest(10000,price_data = pd.DataFrame())
        self.assertTrue(results.attribution.empty)


class Backtester2:
    def __init__(self, strategy: Strategy):
        self.strategy = strategy
        self.position_pnls = []

    def backtest(self, capital, price_data : pd.DataFrame, commission_per_k=0.0):
        self.context = BacktestContext(capital, price_data.columns.values)
        self.context.pnl = pd.Series(capital,index=price_data.index.values)
        self.context.commission_per_k = commission_per_k
        backtest_results = BacktestResults()

        if len(price_data.index) < 2 :
            return backtest_results

        t_slice = price_data.index.values[0]
        for index, row in price_data.iloc[1:,:].iterrows():
            capital = self.context.pnl[t_slice]
            for currency in price_data.columns.values:
                data_ser = price_data.ix[:index,currency]
                positions :List[Position] = self.context.positions[currency]
                instruction = self.strategy.schedule(positions, data_ser,self.context)

                if positions == [] and instruction != None:
                    positions.append(Position(instruction, self.context.capital,commission_per_k))
                elif positions != [] and instruction != None:
                    positions[-1].revalue_position(instruction,price_data[index,currency],capital)

                nom_returns = sum([p.pnl_history[-1] for p in positions])
                self.context.attribution.loc[index,currency] = nom_returns
                capital = capital+nom_returns
                self.context.pnl.loc[index] = capital
            t_slice = index
        backtest_results.pnl = self.context.pnl
        backtest_results.attribution = self.context.attribution

        return backtest_results


class BacktestResults:
    def __init__(self):
        self.attribution: pd.DataFrame = pd.DataFrame()
        self.pnl = pd.DataFrame()
        self.headlinePnL = 0


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
                                           data_ser.name, data_ser[-1].date)


        if data_ser[-2].open >= avg[-2] and todays_price_ < avg[-1]:
            instruction = TradeInstruction(todays_price_, todays_price_ + as_price(self.stop_value, data_ser.name),
                                           self.risk_per_trade,
                                           data_ser.name, data_ser[-1].date)

        return instruction

    def run(self, rates):
        pass
