import time

import numpy as np
import pandas as pd
import sys

from core import TradeLine, Backtester, FREDDataProvider, plot_data
from strategy import StrengthMomentum

if __name__ == "__main__":
    # t21 = TradeLine(1.8030, 1.8000, -30, 0.01, cur, None)
    cur = 'EURUSD'
    tl0 = TradeLine(1.8000, np.nan, 0, 0, cur, None)
    tl01 = TradeLine(1.8000, np.nan, 0, 0, cur, None)
    tl1 = TradeLine(1.8000, 1.7980, -20, 0.005, cur, None)
    t21 = TradeLine(1.8030, 1.8000, -30, 0.01, cur, None)
    t31 = TradeLine(1.8080, 1.8000, -30, -0.03, cur, None)
    line_dem = [tl0, tl01, tl1, t21, t31]
    cap1 = 10000
    dff = pd.DataFrame(index=pd.date_range('2012-01-01', '2012-01-05'), data=line_dem, columns=[cur])
    bt = Backtester.backtest(cap1, dff)
    strat = StrengthMomentum(lookback=2)
    dp = FREDDataProvider()
    my_bt = Backtester(dp, strat)
    result = my_bt.full_backtest(10000, ('2004-01-01', time.strftime("%c")))
    plot_data(result.PnL)
