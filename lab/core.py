from abc import ABCMeta, abstractmethod
from enum import Enum

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import quandl as qdl

qdl.ApiConfig.api_key = '61oas6mNaNKgDAh27k1x'


class InitError(Exception): pass


class DataProvider(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_rates(self):
        raise NotImplementedError('Must implement get_rates()')


class Direction(Enum):
    Short = -1
    Long = 1


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


class TradeLine():
    def __init__(self, price, stop, stop_pips, risk, currency, trade_date):
        self.currency = currency
        self.price = price
        self.stop = stop
        self.stop_pips = stop_pips
        self.risk = risk
        self.trade_date = trade_date

    def __repr__(self):
        return 'p=%s, s=%s, r=%s' % (self.price, self.stop, self.risk)


class Transaction:
    def __init__(self, trade_details, capital, spread=0, commission_per_k=0.0):
        self.pip_value = 0.1
        self.historic_pnl = []
        self.commission_per_k = commission_per_k
        self.trade_details = trade_details
        self.spread = spread
        self.risk = trade_details.risk
        self.last_observed_price = trade_details.price
        self.direction = Direction.Long if trade_details.risk > 0 else Direction.Short
        spread_as_price = as_price(spread,trade_details.currency)
        self.fill_price = self.trade_details.price + (
            -spread_as_price if self.direction is Direction.Long else spread_as_price)
        fill_details = self.calc_position_size_in_k(capital)
        self.position_sz = fill_details[0]
        self.pnl = (-self.calculate_transaction_cost() * 2) + (
            self.value_since_last_observation(self.fill_price, self.trade_details.price))
        # We Calculate transaction costs for getting in and out upfront
        self.true_stop_pips = fill_details[1]
        self.validate_construction()

    def calculate_transaction_cost(self, position_to_close=None):
        position_to_close = self.position_sz if position_to_close is None else position_to_close
        return self.commission_per_k * abs(position_to_close)

    def validate_construction(self):
        if self.direction is Direction.Long and (
                    self.trade_details.price < self.trade_details.stop) or self.direction is Direction.Short and (
                    self.trade_details.price > self.trade_details.stop):
            raise InitError("Transaction inconsistent Dir:%s P:%s S:%s" % (
                self.direction, self.trade_details.price, self.trade_details.stop))

    def is_closed(self):
        return self.risk == 0

    @property
    def pnl(self):
        return self.historic_pnl[-1]

    @pnl.setter
    def pnl(self, value):
        self.historic_pnl.append(value)

    '''Assumption: price has no spread. Usage: to use potion size we say that if position size
    of 50k is worked out then for each pip move we make/lose 5 or 50*0.1'''

    def calc_position_size_in_k(self, capital, trade_friction_func=lambda x: x):
        if self.trade_details.price == self.trade_details.stop or capital < 0:
            return 0, 0

        # direction_multiplier = 1 if self.direction is Direction.Long else -1
        stop_pips = get_pips(self.trade_details.price - self.trade_details.stop,self.trade_details.currency)
        friction_pips = trade_friction_func(stop_pips)
        position_size_in_k = (capital * self.risk) / (abs(friction_pips) * self.pip_value)
        return (round(position_size_in_k, 0), friction_pips)

    def __repr__(self):
        return "p: %s k: %s pnl: %s r:%s" % (
            self.trade_details.price, self.position_sz, self.pnl, self.risk)

    def value_since_last_observation(self, price, delta_price=np.NaN, position_nominal=np.NaN):
        position_nominal = self.position_sz if np.isnan(position_nominal) else position_nominal
        delta_price = self.last_observed_price if np.isnan(delta_price) else delta_price
        price_difference = price - delta_price
        pip_difference = get_pips(price_difference, self.trade_details.currency)
        return pip_difference * position_nominal * self.pip_value

    def close_transaction(self, price, risk_to_close=np.NaN):
        spread_as_price = as_price(self.spread, self.trade_details.currency)

        fill_price = price + (-spread_as_price if self.direction is Direction.Long else spread_as_price)

        if self.risk == 0:
            return 0

        risk_to_close = -self.risk if np.isnan(
            risk_to_close) else risk_to_close
        position_sz_to_close = (risk_to_close / self.risk) * self.position_sz

        self.validate_close(risk_to_close)

        pnl_to_close = self.value_since_last_observation(fill_price, self.trade_details.price, -position_sz_to_close)
        # pnl_to_close -= self.calculate_transaction_cost(position_sz_to_close)
        self.pnl = pnl_to_close
        self.position_sz += position_sz_to_close
        self.risk += risk_to_close
        return self.pnl

    def validate_close(self, risk_to_close):
        if self.direction is Direction.Short and risk_to_close < 0 or \
                                self.direction is Direction.Long and risk_to_close > 0:
            raise RuntimeError(
                'Currency %s Cannot close out %s trade for %s risk on date %s with risk %s' %
                (self.trade_details.currency, self.direction, risk_to_close, self.trade_details.trade_date, self.risk))
        if abs(risk_to_close) > abs(self.risk):
            raise RuntimeError('Currency: %s on date %s Cannot over run risk' %
                               (self.trade_details.currency, self.trade_details.trade_date))

    @abstractmethod
    def no_friction(self, x):
        return x


class Position:
    def __init__(self, initiating_line, capital, commission_per_k=0.0, spread=0.0):
        if initiating_line.risk == 0:
            raise LookupError('cannot initiate holding with no risk')

        trsction = Transaction(initiating_line, capital, commission_per_k=commission_per_k,spread=spread)
        self.lines = [trsction]
        self.commission_per_k = commission_per_k
        self.spread = spread
        self.pnl_history = [0]
        self.currency = initiating_line.currency
        # self.net_direction = trsction.direction

    @property
    def net_direction(self):
        return None if not self.lines else self.lines[-1].direction

    def close_stop_outs(self, price):
        running_pnl = 0
        for line in self.lines:
            short_stopped_out = line.direction is Direction.Short and price > line.trade_details.stop
            long_stopped_out = line.direction is Direction.Long and price < line.trade_details.stop
            if short_stopped_out or long_stopped_out:
                line.pnl = line.value_since_last_observation(line.trade_details.stop, line.trade_details.price)
                line.risk = 0
                running_pnl += line.pnl
        return running_pnl

    def revalue_position(self, trade_line, current_capital):

        if trade_line.currency != self.currency:
            raise LookupError('Currencies do not match')

        pnl_line = Transaction(trade_line, current_capital, commission_per_k=self.commission_per_k, spread=self.spread)
        locked_in_pnl = 0
        locked_in_pnl += self.close_stop_outs(trade_line.price)

        if abs(pnl_line.risk) > 0 and (self.net_direction is None or self.net_direction == pnl_line.direction):
            locked_in_pnl = pnl_line.pnl
            self.lines.append(pnl_line)
        else:
            residual_risk = trade_line.risk
            while abs(residual_risk) > 0:
                if not self.lines:
                    trade_line.risk = residual_risk
                    pnl_line = Transaction(trade_line, current_capital, commission_per_k=self.commission_per_k, spread=self.spread)
                    locked_in_pnl += pnl_line.pnl
                    self.lines.append(pnl_line)
                    residual_risk = 0
                else:
                    for line in self.lines:
                        # fully close out the trade else partially close out
                        if abs(residual_risk) > abs(line.risk):
                            residual_risk += line.risk
                            locked_in_pnl += line.close_transaction(price=trade_line.price)
                            self.lines.remove(line)
                        else:
                            locked_in_pnl += line.close_transaction(trade_line.price, residual_risk)
                            if line.risk == 0:
                                self.lines.remove(line)
                            residual_risk = 0

        self.pnl_history.append(locked_in_pnl)
        return locked_in_pnl


class Backtester:
    def __init__(self, dataprovider, strategy):
        self.dataprovider = dataprovider
        self.strategy = strategy

    @staticmethod
    def spread_map():
        return {'EURUSD': 1.5, 'AUDUSD': 1.5, 'USDJPY': 1.7, 'USDCAD': 2.5, 'GBPUSD': 2.2,
                'NZDUSD': 1.8, 'USDCHF': 2.0, 'USDBRL': 5.0, 'USDCNY': 8.0,
                'USDDKK': 10.0, 'USDHKD': 4.0, 'USDINR': 10.5, 'USDMXN': 230.0, 'USDTWD': 10.0,
                'USDNOK': 40.0, 'USDSGD': 3.8, 'USDSEK': 40.0}

    @staticmethod
    def get_spread(spread_map, currency):
        if spread_map is None:
            return 0.0
        else:
            return spread_map[currency]

    @staticmethod
    def calculate_position(current_holding, today, capital, commission_per_k, currency, spread_map=None):
        spread = Backtester.get_spread(spread_map,currency)
        if np.isnan(today.stop): return current_holding
        today_has_risk = not np.isnan(today.risk) and today.risk != 0

        if current_holding is None and today_has_risk:
            return Position(today, capital, commission_per_k,spread)

        if current_holding is None and not today_has_risk:
            return None
        else:
            current_holding.revalue_position(today, capital)
            return current_holding

    @staticmethod
    def backtest(capital, trade_details_df, commission_per_k=0.0, spread_map=None):
        backtest_results_df = pd.DataFrame(index=trade_details_df.index.values, columns=trade_details_df.columns.values)
        backtest_results_df = backtest_results_df.where((pd.notnull(backtest_results_df)), None)
        last_t = trade_details_df.index.values[0]
        backtest_results_df.set_value(last_t, 'PnL', capital)
        for t in trade_details_df.index.values[1:]:
            current_capital = backtest_results_df.ix[last_t, 'PnL']
            for currency in trade_details_df.columns.values:
                todays_details = trade_details_df.ix[t, currency]
                current_position = backtest_results_df.ix[last_t, currency]

                current_position = Backtester.calculate_position(current_position, todays_details, capital,
                                                                 commission_per_k, currency, spread_map)

                if current_position is not None:
                    current_capital += current_position.pnl_history[-1]

                backtest_results_df.set_value(t, currency, current_position)

            backtest_results_df.set_value(t, 'PnL', current_capital)
            last_t = t
        return backtest_results_df

    def full_backtest(self, capital, commission_per_k=0.0, date_range=None, use_spread=True):
        rates = self.dataprovider.get_rates() if date_range is None else get_range(self.dataprovider.get_rates(),
                                                                                   date_range[0], date_range[1])
        trade_details = self.strategy.run(rates)

        spread_map =  Backtester.spread_map() if use_spread else None

        return self.backtest(capital, trade_details, commission_per_k,spread_map)


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
            td = TradeLine(price=price_df.ix[i, c], stop=stop_df.ix[i, c], stop_pips=pips_df.ix[i, c],
                           risk=rolling_risk_df.ix[i, c], currency=c, trade_date=i)
            trade_details_df.set_value(i, c, td)
    return trade_details_df
