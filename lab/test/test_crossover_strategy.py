import datetime as dt
import unittest as ut

import numpy as np
import pandas as pd

from lab import Ohlc
from lab.indicators.ema import EMA
from lab.strategy.strategy import Strategy


def date_range(numdays, date=dt.datetime(2016, 10, 20)):
    return [date + dt.timedelta(days=x) for x in range(0, numdays)]


class CrossOverStrategyTests(ut.TestCase):

    def test_can_initialise(self):
        crossover = CrossOverStrategy(40,10)
        self.assertTrue(True)

    def test_cannot_initialise_without_parameters(self):
        with self.assertRaises(Exception):
            crossover = CrossOverStrategy()

    # def test_when_fast_crosses_over_slow_some_trade_is_generated(self):
    #     ser = pd.Series([Ohlc(50.19, 50.19, 49.87, 50.13),
    #                      Ohlc(50.12, 50.12, 49.20, 49.53),
    #                      Ohlc(49.66, 49.66, 48.90, 49.50),
    #                      Ohlc(49.88, 49.88, 49.43, 49.75),
    #                      Ohlc(50.19, 50.19, 49.73, 50.03),
    #                      Ohlc(50.04, 50.46, 49.97, 50.40),
    #                      Ohlc(50.45, 50.59, 49.97, 50.40),
    #                      Ohlc(50.55, 50.80, 49.97, 50.40),
    #                      Ohlc(50.07, 51.07, 49.97, 50.40),
    #                      Ohlc(51.04, 50.69, 49.97, 50.40),
    #                      Ohlc(50.84, 51.27, 49.97, 50.40),
    #                      Ohlc(50.70, 51.18, 49.97, 50.40),
    #                      Ohlc(51.34, 51.60, 49.97, 50.40)
    #                      ], index=date_range(6))


class CrossOverStrategy(Strategy):

    def __init__(self, slowMA, fastMa):
        self.slowMA = slowMA
        self.fastMA = fastMa


    def run(self, rates):
        pass
