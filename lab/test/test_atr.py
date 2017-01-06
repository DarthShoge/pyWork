import unittest
import pandas as pd
import datetime as dt
from lab.indicators.indicator import ATR
from lab.core.structures import Ohlc


def date_range(numdays, date =dt.datetime(2016, 10, 20)):
    return [date + dt.timedelta(days=x) for x in range(0, numdays)]


class ATRTests(unittest.TestCase):

    def test_series_with_only_one_price_point_should_calculate_with_hi_minus_low(self):
        sut = ATR()
        ser = pd.Series([Ohlc(1.5, 1.6, 1.4, 1.55)], index=date_range(1))
        atr = sut.calculate(ser)
        self.assertAlmostEqual(0.2,atr)

    def test_series_with_two_points_should_use_gapping_low_to_previous_close_if_maximum_size(self):
        sut = ATR()
        ser = pd.Series([Ohlc(1.5, 1.6, 1.4, 1.5),
                         Ohlc(1.0, 1.3, 1.0, 1.3)], index=date_range(2))
        atr = sut.calculate(ser)
        self.assertAlmostEqual(0.35,atr)

    def test_series_with_two_points_should_use_gapping_hi_to_previous_close_if_maximum_size(self):
        sut = ATR()
        ser = pd.Series([Ohlc(1.5, 1.6, 1.4, 1.5),
                         Ohlc(2.0, 2.0, 1.8, 1.8)], index=date_range(2))
        atr = sut.calculate(ser)
        self.assertAlmostEqual(0.35,atr)

    def test_should_use_average_to_calculate_using_period_size_then_shoudl_calulate_correctly(self):
        sut = ATR(periods=5)
        ser = pd.Series([Ohlc(50.19, 50.19, 49.87, 50.13),
                         Ohlc(50.12, 50.12, 49.20, 49.53),
                         Ohlc(49.66, 49.66, 48.90, 49.50),
                         Ohlc(49.88, 49.88, 49.43, 49.75),
                         Ohlc(50.19, 50.19, 49.73, 50.03)], index=date_range(5))
        atr = sut.calculate(ser)
        self.assertAlmostEqual(0.584,atr)

    def test_should_uses_exponential_average_to_calculate_using_period_size_then_shoudl_calulate_correctly(self):
        sut = ATR(periods=5)
        ser = pd.Series([Ohlc(50.19, 50.19, 49.87, 50.13),
                         Ohlc(50.12, 50.12, 49.20, 49.53),
                         Ohlc(49.66, 49.66, 48.90, 49.50),
                         Ohlc(49.88, 49.88, 49.43, 49.75),
                         Ohlc(50.19, 50.19, 49.73, 50.03),
                         Ohlc(50.36, 50.36, 49.26, 50.31)], index=date_range(6))
        atr = sut.calculate(ser)
        self.assertAlmostEqual(0.6872,atr)