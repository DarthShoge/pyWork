import pandas as pd
import numpy as np
from abc import ABCMeta, abstractmethod


class Indicator(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def calculate(self, price_ser):
        raise NotImplementedError('Must implement calculate()')

    @abstractmethod
    def calculate_dataframe(self, price_ser):
        raise NotImplementedError('Must implement calculate_dataframe()')


class ATR(Indicator):

    def __init__(self, periods=14):
        self.periods=periods

    def calculate(self, price_ser):
        t_minus1 = price_ser.shift(1)
        calc_df = pd.DataFrame({'t-1': t_minus1, 't': price_ser})
        calc_df['tr'] = calc_df.apply(lambda x : self.true_range(x['t'], x['t-1']), axis=1)
        calc_df['atr'] = np.nan

        if len(calc_df) < self.periods:
            return calc_df['tr'].mean()

        calc_df.ix[self.periods - 1, 'atr'] = calc_df.ix[0:self.periods, 'tr'].mean()
        for i in range(self.periods, len(calc_df)):
            calc_df.ix[i, 'atr'] = (calc_df.ix[i-1, 'atr'] * (self.periods - 1) + calc_df.ix[i, 'tr']) / self.periods

        return calc_df.ix[-1, 'atr']

    def calculate_dataframe(self, price_ser):
        t_minus1 = price_ser.shift(1)
        calc_df = pd.DataFrame({'t-1': t_minus1, 't': price_ser})
        calc_df['tr'] = calc_df.apply(lambda x : self.true_range(x['t'], x['t-1']), axis=1)
        calc_df['atr'] = np.nan

        if len(calc_df) < self.periods:
            return calc_df['tr'].mean()

        calc_df.ix[self.periods - 1, 'atr'] = calc_df.ix[0:self.periods, 'tr'].mean()
        for i in range(self.periods, len(calc_df)):
            calc_df.ix[i, 'atr'] = (calc_df.ix[i-1, 'atr'] * (self.periods - 1) + calc_df.ix[i, 'tr']) / self.periods

        return calc_df

    def true_range(self, t, t_minus_1):
        hl = t.high - t.low
        has_t_minus_1 = not isinstance(t_minus_1, float) or not np.isnan(t_minus_1)
        il = abs(t.high - t_minus_1.close) if has_t_minus_1 else 0
        ih = abs(t.low - t_minus_1.close) if has_t_minus_1 else 0
        return max(hl, il, ih)

