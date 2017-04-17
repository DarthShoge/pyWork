from lab import Ohlc
import datetime as dt
import pandas as pd


def ohcl(o, c, h, l):
    return Ohlc(o, h, l, c, dt.datetime.today())


def date_range(numdays, date=dt.datetime(2016, 10, 20)):
    return [date + dt.timedelta(days=x) for x in range(0, numdays)]


def ohlc_series(data,name = 'TEST'):
    range = date_range(len(data))
    ser = pd.Series(data, range, name=name)
    return ser

