import unittest as ut

import numpy as np
import pandas as pd

from lab import Ohlc
from lab.indicators.ema import EMA
from lab.test.test_crossover_strategy import date_range


class EMATests(ut.TestCase):
    def test_series_with_less_than_time_frame_then_price_point_should_nan(self):
        sut = EMA(periods=10)
        ser = pd.Series([Ohlc(50.19, 50.19, 49.87, 50.13),
                         Ohlc(50.12, 50.12, 49.20, 49.53),
                         Ohlc(49.66, 49.66, 48.90, 49.50),
                         Ohlc(49.88, 49.88, 49.43, 49.75),
                         Ohlc(50.19, 50.19, 49.73, 50.03)], index=date_range(5))
        ema = sut.calculate(ser)
        self.assertTrue(np.isnan(ema))

    def test_series_within_time_frame_then_price_point_should_calculate_correctly(self):
        sut = EMA(periods=5)
        ser = pd.Series([Ohlc(50.19, 50.19, 49.87, 50.13),
                         Ohlc(50.12, 50.12, 49.20, 49.53),
                         Ohlc(49.66, 49.66, 48.90, 49.50),
                         Ohlc(49.88, 49.88, 49.43, 49.75),
                         Ohlc(50.19, 50.19, 49.73, 50.03)], index=date_range(5))
        ema = sut.calculate(ser)
        self.assertAlmostEqual(49.788, ema)

    def test_series_should_calculate_correctly_with_single_ema(self):
        sut = EMA(periods=5)
        ser = pd.Series([Ohlc(50.19, 50.19, 49.87, 50.13),
                         Ohlc(50.12, 50.12, 49.20, 49.53),
                         Ohlc(49.66, 49.66, 48.90, 49.50),
                         Ohlc(49.88, 49.88, 49.43, 49.75),
                         Ohlc(50.19, 50.19, 49.73, 50.03),
                         Ohlc(50.04, 50.46, 49.97, 50.40)], index=date_range(6))
        ema = sut.calculate(ser)
        self.assertAlmostEqual(49.992, ema)