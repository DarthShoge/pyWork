import time
import lab as lb
import requests

print(requests.get('http://www.yahoo.com'))

if __name__ == "__main__":
    cap1 = 10000
    strat = lb.StrengthMomentum(lookback=2,max_risk=0.1)
    strat.stop_price_def = lambda x, y: strat.calc_stop_prices(x, y, short_avg_period=3)
    dp = lb.FREDDataProvider(use_exotics=False)
    my_bt = lb.Backtester(dp, strat)

    from_date = '2011-01-01'
    to_date = time.strftime("%c")
    # rates = lb.get_range(dp.get_rates(),from_date,'2011-02-20')
    # h = strat.run_with_diagnostics(rates)
    result = my_bt.full_backtest(10000, commission_per_k=0.06,date_range=('2004-01-01', time.strftime("%c")))
    lb.plot_data(result.PnL)
