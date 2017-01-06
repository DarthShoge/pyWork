import requests
import datetime as dt
import pandas as pd
import numpy as np
from lab.core.structures import Ohlc
from lab.data.dataprovider import DataProvider


def html_encode_numbers(arr):
    return tuple([str(a) if a > 9 else '0' + str(a) for a in arr])


class OandaDataProvider(DataProvider):

    def __init__(self, from_date, to_date, granularity):
        self.from_date = from_date
        self.to_date = to_date
        self.granularity = granularity

    '''
    gets currencies from oanda see for more information such as the different time granularities
    http://developer.oanda.com/rest-live/rates/#getCurrentPrices
    '''
    def get_rates(self):
        all_rates = [self.get_rate(cur, self.from_date, self.to_date, self.granularity) for cur in self.majors()]
        all_rates_df = pd.DataFrame(all_rates[0])
        for df in all_rates[1:]:
            all_rates_df = all_rates_df.join(df)

        all_rates_df.ffill(inplace=True)
        all_rates_df.bfill(inplace=True)
        return all_rates_df

    def get_rate(self, currency, from_date=None, to_date=None, granularity='D'):
        t = html_encode_numbers(to_date.timetuple()[:6])
        f = html_encode_numbers(from_date.timetuple()[:6])
        format_from = '' if from_date is None else ('&start=%s-%s-%sT%s:%s:%sZ' % f).replace(':','%3A')
        format_to = '' if to_date is None else ('&end=%s-%s-%sT%s:%s:%sZ' % t).replace(':','%3A')
        format_currency = currency[:3] + '_' + currency[3:]
        url = "https://api-fxtrade.oanda.com/v1/candles?instrument=%s%s%s&candleFormat=midpoint&granularity=%s" % \
              (format_currency, format_from, format_to, granularity)
        headers = {"Content-Type": "application/json"}
        js = requests.get(url, headers=headers).json()
        candles = js['candles']
        rates = [self.parse_candle(candle) for candle in candles]
        rate_dict = dict(zip([a.date for a in rates], rates))
        rate_ser = pd.Series(rate_dict, name=currency)
        return rate_ser

    @staticmethod
    def parse_candle(candle):
        price_type = 'Mid'
        o = candle['open' + price_type]
        h = candle['high' + price_type]
        l = candle['low' + price_type]
        c = candle['close' + price_type]
        d = np.datetime64(dt.datetime.strptime(candle['time'], '%Y-%m-%dT%H:%M:%S.%fZ'))
        return Ohlc(o, h, l, c, d)
