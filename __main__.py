import time

import numpy as np
import pandas as pd

import lab as lb

if __name__ == "__main__":
    cur = 'EURUSD'
    tl0 = lb.TradeLine(1.8000, np.nan, 0, 0, cur, None)
    tl01 = lb.TradeLine(1.8000, np.nan, 0, 0, cur, None)
    tl1 = lb.TradeLine(1.8000, 1.7980, -20, 0.005, cur, None)
    t21 = lb.TradeLine(1.8030, 1.8000, -30, 0.01, cur, None)
    t31 = lb.TradeLine(1.8080, 1.8000, -30, -0.03, cur, None)
    line_dem = [tl0, tl01, tl1, t21, t31]
    cap1 = 10000
    dff = pd.DataFrame(index=pd.date_range('2012-01-01', '2012-01-05'), data=line_dem, columns=[cur])
    bt = lb.Backtester.backtest(cap1, dff)
    strat = lb.StrengthMomentum(lookback=2,max_risk=0.1)
    strat.stop_price_def = lambda x, y: strat.calc_stop_prices(x, y, short_avg_period=3)
    dp = lb.FREDDataProvider(use_exotics=False)
    my_bt = lb.Backtester(dp, strat)
    result = my_bt.full_backtest(10000, ('2011-01-01', time.strftime("%c")))
    lb.plot_data(result.PnL)
