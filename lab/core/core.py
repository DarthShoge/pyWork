from enum import Enum

import matplotlib.pyplot as plt
import pandas as pd
import quandl as qdl


class InitError(Exception): pass


class Direction(Enum):
    Short = -1
    Long = 1


class TradeInstruction:
    def __init__(self, price, stop, risk, currency, trade_date):
        self.currency = currency
        self.price = price
        self.stop = stop
        self.risk = risk
        self.trade_date = trade_date

    def __repr__(self):
        return 'p=%s, s=%s, r=%s' % (self.price, self.stop, self.risk)


def get_currency_dataframe(cur):
    return qdl.get('BOE/' + cur)


def print_full(x):
    pd.set_option('display.max_rows', len(x))
    print(x)
    pd.reset_option('display.max_rows')


def read_raw_data():
    df = pd.read_csv('EURGBPUSDJPY.csv', index_col='Date', parse_dates=True)
    return df.sort(ascending=True)


def plot_data(df, title="closing prices", normalize=False):
    normalizeddf = df / df.ix[0, :]
    if (normalize):
        plotted = normalizeddf.plot(title=title)
    else:
        plotted = df.plot(title=title)
    plotted.set_xlabel("Date")
    plotted.set_ylabel("Security")
    plt.show()


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


def get_range(df, start, end):
    dates = pd.date_range(start, end)
    indexFrame = pd.DataFrame(index=dates)
    jointFrame = indexFrame.join(df, how='inner')
    return jointFrame


def calc_expected_prc_pos(risk, max_rank, x, risk_boundary=4):
    x_invert = x - (max_rank + 1)
    if 0 < x < risk_boundary:
        return risk / x
    elif x_invert > -risk_boundary < 0:
        return risk / x_invert
    else:
        return 0.0


def get_currency_pair_tuple(pair):
    return (pair[0:3], pair[3:6])


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


def get_pips(value, currency=None):
    currency = currency if currency else value.name
    trade, contra = get_currency_pair_tuple(currency)
    if (contra == 'JPY'):
        return value * 100
    else:
        return value * 10000


def as_price(value, currency=None):
    if value == 0:
        return 0.0

    currency = currency if currency else value.name
    trade, contra = get_currency_pair_tuple(currency)
    if contra == 'JPY':
        return value / 100
    else:
        return value / 10000


def price_data_to_trade_lines(price_df, rolling_risk_df, stop_df, pips_df):
    trade_details_df = pd.DataFrame(index=price_df.index.values, columns=price_df.columns.values)
    for i in trade_details_df.index.values:
        for c in trade_details_df.columns.values:
            td = TradeInstruction(price=price_df.ix[i, c], stop=stop_df.ix[i, c], risk=rolling_risk_df.ix[i, c], currency=c,
                                  trade_date=i)
            trade_details_df.set_value(i, c, td)
    return trade_details_df
