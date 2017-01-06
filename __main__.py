import time
import lab as lb
import datetime as dt
import matplotlib.pyplot as plt
import numpy as np

if __name__ == "__main__":
    cap1 = 10000
    strat = lb.StrengthMomentum(lookback=2, max_risk=0.05)
    strat.stop_price_def = lambda x, y: strat.calc_stop_prices(x, y, short_avg_period=3)
    dp = lb.FREDDataProvider(use_exotics=False)
    oanda = lb.OandaDataProvider(dt.date(2012, 1, 1), dt.date(2013, 1, 1), "D")
    my_bt = lb.Backtester(oanda, strat)
    from_date = '2011-01-01'
    to_date = time.strftime("%c")
    # rates = lb.get_range(dp.get_rates(),from_date,'2011-02-20')
    # h = strat.run_with_diagnostics(rates)
    backtest = my_bt.full_backtest(10000)

    result = backtest[0]
    lb.plot_data(result.PnL)
    rets = [x.returns for x in backtest[1] if x is not None]
    plt.hist(rets,bins='auto')
    pns = [x.pnl for x in backtest[1] if x is not None]

    result = my_bt.full_backtest(10000, date_range=('2004-01-01', time.strftime("%c")), use_spread=False)
    lb.plot_data(result.PnL)
