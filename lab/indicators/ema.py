import numpy as np
import pandas as pd

from lab import Indicator


class EMA(Indicator):
    def __init__(self, periods=10):
        self.periods = periods
        self.smoothing_const = 2 / (periods + 1)

    def calculate(self, price_ser):
        return self.calculate_dataframe(price_ser).ix[-1,'ema']

    def calculate_dataframe(self, price_ser):
        ser = price_ser.apply(lambda x: x.close)
        n_period_sma = ser.rolling(self.periods).mean()
        calc_df = pd.DataFrame({'price': ser, 'sma': n_period_sma})
        calc_df['ema'] = np.nan

        if len(calc_df) < self.periods:
            return calc_df

        calc_df.ix[self.periods - 1, 'ema'] =calc_df.ix[self.periods - 1, 'sma']
        for i in range(self.periods, len(calc_df)):
            c = calc_df.ix[i]
            last_ema = calc_df.ix[i-1, 'ema']
            calc_df.ix[i, 'ema'] = self.smoothing_const * (c['price'] - last_ema) + last_ema

        return calc_df