from abc import ABCMeta, abstractmethod
from typing import List

import numpy as np
import pandas as pd

from lab.core.position import Position
from lab.core.structures import BacktestContext
from lab.indicators.indicator import ATR


class Strategy(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def run(self, rates):
        raise NotImplementedError('Must implement run()')

    @abstractmethod
    def schedule(self, positions: List[Position], data_ser: pd.Series, context : BacktestContext):
        raise NotImplementedError('Must implement schedule()')


class ATRCalcDef:
    def __init__(self, multiplier):
        self.multiplier = multiplier

    def calc_stop_prices(self, risk_df, price_df, periods=7):
        atr = ATR(periods=periods)
        stop_df = pd.DataFrame(index=price_df.index, columns=price_df.columns)
        for col in stop_df.columns:
            atr_df = atr.calculate_dataframe(price_df[col]).shift(1)
            atr_df['true_atr'] = risk_df[col].apply(lambda x: np.sign(x)) * atr_df['atr'] * self.multiplier
            stop_df[col] = atr_df['true_atr']
        return price_df.applymap(lambda x: x.open) - stop_df
