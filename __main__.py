import time
import lab as lb
import datetime as dt
import matplotlib.pyplot as plt
import numpy as np
#import scipy
import statsmodels.api as sm

from lab.strategy.strategy import ATRCalcDef


if __name__ == "__main__":
    cap1 = 10000
    calc_def = ATRCalcDef(multiplier=2)
    strat = lb.LineReg_Tf(lookback=126)
    # strat = lb.StrengthMomentum.StrengthMomentum(lookback=31, max_risk=0.05)
    strat.stop_price_def = lambda x, y: calc_def.calc_stop_prices(x, y, periods=14)
    dp = lb.FREDDataProvider(use_exotics=False)
    oanda = lb.OandaDataProvider(dt.date(2010, 1, 1), dt.date(2015, 1, 1), "D")
    # price_df = oanda.get_rates()
    my_bt = lb.Backtester(oanda, strat)
    from_date = '2011-01-01'
    to_date = time.strftime("%c")
    # rates = lb.get_range(dp.get_rates(),from_date,'2011-02-20')
    # h = strat.run_with_diagnostics(oanda.get_rates())
    backtest = my_bt.full_backtest(10000)

    result = backtest[0]
    lb.plot_data(result.PnL)
    rets = [x.returns for x in backtest[1] if x is not None and x is not np.isnan(x.returns)]
    plt.hist(rets, bins='auto')
    pns = [x.pnl for x in backtest[1] if x is not None]

    win_pct = len([ x for x in pns if x > 0.1]) / len(pns)

    result = my_bt.full_backtest(10000, date_range=('2004-01-01', time.strftime("%c")), use_spread=False)
    lb.plot_data(result.PnL)




