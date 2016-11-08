from abc import ABCMeta, abstractmethod

import numpy as np

from lab.core import calc_real_risk, get_pips, get_currency_pair_tuple, get_relative_returns, get_rolling_weighted_returns, \
    calc_expected_prc_pos, convert_to_natural_pair_df, price_data_to_trade_lines


class Strategy(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def run(self, rates):
        raise NotImplementedError('Must implement run()')


class StrengthMomentum(Strategy):
    def __init__(self, lookback=5, risk_per_trade=0.01, max_risk=0.05, stop_price_def=None):
        self.stop_price_def = self.calc_stop_prices if stop_price_def is None else stop_price_def
        self.lookback = lookback
        self.risk_per_trade = risk_per_trade
        self.max_risk = max_risk

    def run(self, rates):
        return self.run_with_diagnostics(rates).trade_details

    @staticmethod
    def calc_rolling_risk(price_df, theoretical_r_df, max_r):
        rows, cols = price_df.shape
        currencies = price_df.columns.values
        rolling_risk_df = theoretical_r_df.copy()
        for currency in currencies:
            p_ser = price_df[currency]
            r_ser = rolling_risk_df[currency]
            for x in range(1, rows):
                expected_r = r_ser[x]
                r_ser[x] = calc_real_risk(p_ser[x], p_ser[x - 1], r_ser[x - 1], expected_r, max_r)
        return rolling_risk_df

    @staticmethod
    def calc_avg_closing_range(data_df, periods, avging_periods):
        return (data_df.rolling(window=periods).max() - data_df.rolling(window=periods).min()).rolling(
            window=avging_periods).mean()

    def calc_stop_prices(self, risk_df, price_df, short_avg_period=7):
        avg_range = self.calc_avg_closing_range(price_df, periods=short_avg_period, avging_periods=28) / 2
        stop_pips_df = avg_range.apply(lambda x: get_pips(x))
        pip_mult_ar = [100 if get_currency_pair_tuple(x)[1] == 'JPY' else 10000 for x in price_df.columns.values]
        stop_as_price_df = (stop_pips_df / pip_mult_ar) * (risk_df.apply(lambda x: np.sign(x)))
        return price_df - stop_as_price_df

    def run_with_diagnostics(self, rates):
        diagnostic = type('', (), {})()
        diagnostic.data_df = rates
        rows, cols = diagnostic.data_df.shape

        diagnostic.relative_returns_df = get_relative_returns(diagnostic.data_df)
        diagnostic.rolling_rel_df = get_rolling_weighted_returns(diagnostic.relative_returns_df, periods=self.lookback)
        diagnostic.ranked_rolling_df = diagnostic.rolling_rel_df.rank(axis=1, ascending=False)
        diagnostic.ranked_rolling_df.fillna(0, inplace=True)
        diagnostic.theoretical_risk = diagnostic.ranked_rolling_df.apply(
            lambda x: x.apply(lambda y: calc_expected_prc_pos(self.risk_per_trade, cols, y)))
        diagnostic.conventional_t_risk = convert_to_natural_pair_df(diagnostic.data_df.columns.values,
                                                                    diagnostic.theoretical_risk)
        diagnostic.rolling_risk = self.calc_rolling_risk(diagnostic.data_df, diagnostic.conventional_t_risk,
                                                         self.max_risk)
        daily_risk = diagnostic.rolling_risk - diagnostic.rolling_risk.shift(1)
        diagnostic.stop_price_df = self.stop_price_def(daily_risk, diagnostic.data_df)
        diagnostic.stop_pips_df = (diagnostic.stop_price_df - diagnostic.data_df).apply(get_pips).fillna(value=0)
        daily_risk.fillna(0, inplace=True)
        diagnostic.trade_details = price_data_to_trade_lines(diagnostic.data_df, daily_risk, diagnostic.stop_price_df,
                                                             diagnostic.stop_pips_df)

        return diagnostic

def calculate_sharpe_ratio(returns, risk_free_rate) :
    return returns

