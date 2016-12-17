from abc import ABCMeta, abstractmethod
from lab.core.structures import Ohlc

import quandl as qdl

qdl.ApiConfig.api_key = '61oas6mNaNKgDAh27k1x'

class DataProvider(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_rates(self):
        raise NotImplementedError('Must implement get_rates()')


class FREDDataProvider(DataProvider):
    def __init__(self, use_exotics=False):

        self.currencies = self.majors()
        if use_exotics:
            self.currencies.update(self.exotics())

    @staticmethod
    def majors():
        return {'EURUSD': 'DEXUSEU',
                'AUDUSD': 'DEXUSAL',
                'USDJPY': 'DEXJPUS',
                'USDCAD': 'DEXCAUS',
                'GBPUSD': 'DEXUSUK',
                'NZDUSD': 'DEXUSNZ',
                'USDCHF': 'DEXSZUS'}

    @staticmethod
    def exotics():
        return {'USDBRL': 'DEXBZUS',
                'USDCNY': 'DEXCHUS',
                'USDCNY': 'DEXCHUS',
                'USDDKK': 'DEXDNUS',
                'USDHKD': 'DEXHKUS',
                'USDINR': 'DEXINUS',
                'USDMXN': 'DEXMXUS',
                'USDTWD': 'DEXTAUS',
                'USDNOK': 'DEXNOUS',
                'USDSGD': 'DEXSIUS',
                'USDSEK': 'DEXSDUS',
                }

    def get_rate(self, currency):
        '''
        Gets currency using cur list found at https://www.quandl.com/blog/api-for-currency-data
        >>> get_rate('DEXUSEU')
        AUDUSD dataframe
        '''
        cur_code = self.currencies[currency]
        currency_df = qdl.get('FRED/' + cur_code)
        currency_df = currency_df.applymap(lambda x: Ohlc(x, x, x, x))
        currency_df.rename(columns={'VALUE': currency}, inplace=True)
        return currency_df

    def get_rates(self):
        holding_dfs = []
        for code in self.currencies.keys():
            holding_dfs.append(self.get_rate(code))

        index_cur_df = holding_dfs[0]

        for df in holding_dfs[1:]:
            index_cur_df = index_cur_df.join(df)

        index_cur_df.ffill(inplace=True)
        index_cur_df.bfill(inplace=True)

        return index_cur_df