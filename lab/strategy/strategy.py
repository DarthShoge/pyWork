from abc import ABCMeta, abstractmethod

import numpy as np
import pandas as pd

from lab.indicators.indicator import ATR
from lab.core.common import get_pips, get_currency_pair_tuple, price_data_to_trade_lines


class Strategy(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def run(self, rates):
        raise NotImplementedError('Must implement run()')

    @abstractmethod
    def schedule(self, positions, data_ser):
        raise NotImplementedError('Must implement schedule()')


class StrengthMomentum(Strategy):
    def schedule(self, positions, data_ser):
        pass

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

    def calc_stop_prices(self, risk_df, rates_df, short_avg_period=7):
        price_df = rates_df.applymap(lambda x: x.open)
        avg_range = self.calc_avg_closing_range(price_df, periods=short_avg_period, avging_periods=28) / 2
        stop_pips_df = avg_range.apply(lambda x: get_pips(x))
        pip_mult_ar = [100 if get_currency_pair_tuple(x)[1] == 'JPY' else 10000 for x in price_df.columns.values]
        stop_as_price_df = (stop_pips_df / pip_mult_ar) * (risk_df.apply(lambda x: np.sign(x)))
        return price_df - stop_as_price_df

    def run_with_diagnostics(self, ohcl_rates):
        rates = ohcl_rates.applymap(lambda x: x.open)
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
        diagnostic.stop_price_df = self.stop_price_def(daily_risk, ohcl_rates)
        diagnostic.stop_pips_df = (diagnostic.stop_price_df - diagnostic.data_df).apply(get_pips).fillna(value=0)
        daily_risk.fillna(0, inplace=True)
        diagnostic.trade_details = price_data_to_trade_lines(diagnostic.data_df, daily_risk, diagnostic.stop_price_df,
                                                             diagnostic.stop_pips_df)

        return diagnostic


def get_returns(df):
    previous_day_df = df.shift(1)
    return (df - previous_day_df) / previous_day_df


def get_base_quote_returns(df, only_benchmark=False, benchmark='USD'):
    rets = get_returns(df)
    col_name = df.columns[0]
    base_cur = col_name[0:3]
    quote_cur = col_name[3:6]
    base_df = rets.copy()
    base_df.columns = [base_cur + quote_cur]
    quote_df = -rets
    quote_df.columns = [quote_cur + base_cur]
    if (only_benchmark):
        if (base_cur == benchmark):
            return_df = base_df
        else:
            return_df = quote_df
        return return_df
    else:
        return pd.concat([base_df, quote_df], axis=1)


def get_relative_returns(data_df, with_benchmark=False):
    returns_df = get_base_quote_returns(data_df[[0]], only_benchmark=True)

    for col in data_df.columns[1:]:
        col_returns_df = get_base_quote_returns(data_df[[col]], only_benchmark=True)
        returns_df = returns_df.join(col_returns_df)

    if (with_benchmark):
        benchmark_ser = returns_df.mean(axis=1)
        benchmark_ser.name = 'USD'
        returns_df = returns_df.join(benchmark_ser)

    return returns_df


def get_rolling_weighted_returns(rel_returns_df, periods):
    return rel_returns_df.rolling(window=periods, center=False).mean()


def calc_expected_prc_pos(risk, max_rank, x, risk_boundary=4):
    x_invert = x - (max_rank + 1)
    if 0 < x < risk_boundary:
        return risk / x
    elif x_invert > -risk_boundary < 0:
        return risk / x_invert
    else:
        return 0.0


def check_not_conventional(contra, conventions):
    return [x for x in conventions if get_currency_pair_tuple(x)[0] == contra]


def convert_to_natural_pair(original_pairs_array, benchmarked_ser):
    benchmark_cur, contra_cur = get_currency_pair_tuple(benchmarked_ser.name)
    is_unnatural = check_not_conventional(contra_cur, original_pairs_array)
    if is_unnatural:
        actual_name = contra_cur + benchmark_cur
        natural_ser = -benchmarked_ser
        natural_ser.rename(actual_name)
        return natural_ser
    else:
        return benchmarked_ser


def convert_to_natural_pair_df(original_pairs_array, df):
    conventional_df = df.apply(lambda x: convert_to_natural_pair(original_pairs_array, x))
    new_cols = []
    for x in conventional_df.columns.values:
        benchmark_cur, contra_cur = get_currency_pair_tuple(x)
        if (check_not_conventional(contra_cur, original_pairs_array)):
            new_cols.append(contra_cur + benchmark_cur)
        else:
            new_cols.append(x)
    conventional_df.columns = new_cols

    return conventional_df


def calc_real_risk(p, p_minus1, current_r, expected_r, max_r):
    max_r_multiplier = max_r * 100
    polarity = -1 if expected_r < 0 else 1
    real_max_r = max_r_multiplier * expected_r
    if (p > p_minus1 and expected_r > 0) or (p < p_minus1 and expected_r < 0):
        risk = (current_r + expected_r)
        return min(abs(risk), abs(real_max_r)) * polarity
    elif (expected_r == 0):
        return 0
    else:
        return min(abs(current_r), abs(real_max_r)) * polarity


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
