import matplotlib.pyplot as plt
import pandas as pd
import quandl as qdl

from lab.core.structures import TradeInstruction


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


def get_range(df, start, end):
    dates = pd.date_range(start, end)
    indexFrame = pd.DataFrame(index=dates)
    jointFrame = indexFrame.join(df, how='inner')
    return jointFrame


def get_currency_pair_tuple(pair):
    return (pair[0:3], pair[3:6])


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
