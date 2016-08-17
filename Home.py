import pandas as pd
import matplotlib.pyplot as plt
import quandl as qdl
import scipy.optimize as sp
import numpy as np
from abc import ABCMeta, abstractmethod
from numbers import Number
from matplotlib.pyplot import plot

qdl.ApiConfig.api_key = '61oas6mNaNKgDAh27k1x'

class DataProvider(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_rates(self):
        raise NotImplementedError('Must implement get_rates()')


class FREDDataProvider(DataProvider):
    def __init__(self):

        self.major_codes = {'EURUSD': 'DEXUSEU',
                            'AUDUSD': 'DEXUSAL',
                            'USDJPY': 'DEXJPUS',
                            'USDCAD': 'DEXCAUS',
                            'GBPUSD': 'DEXUSUK',
                            'NZDUSD': 'DEXUSNZ',
                            'USDCHF': 'DEXSZUS'}

    def get_rate(self, currency):
        '''
        Gets currency using cur list found at https://www.quandl.com/blog/api-for-currency-data
        >>> get_rate('DEXUSEU')
        AUDUSD dataframe
        '''
        cur_code = self.major_codes[currency]
        currency_df = qdl.get('FRED/' + cur_code)
        currency_df.rename(columns={'VALUE': currency}, inplace=True)
        return currency_df

    def get_rates(self):
        holding_dfs = []
        for code in self.major_codes.keys():
            holding_dfs.append(self.get_rate(code))

        index_cur_df = holding_dfs[0]

        for df in holding_dfs[1:]:
            index_cur_df = index_cur_df.join(df)

        index_cur_df.ffill(inplace=True)
        index_cur_df.bfill(inplace=True)

        return index_cur_df

class TradeLine() :

    def __init__(self,price,stop,stop_pips,risk,currency,trade_date):
        self.currency = currency
        self.price = price
        self.stop = stop
        self.stop_pips = stop_pips
        self.risk = risk
        self.trade_date = trade_date

    def __repr__(self):
        return 'p=%s, s=%s, r=%s' % (self.price,self.stop,self.risk)


class PnLLine() :
    def __init__(self,trade_details,capital):
        self.trade_details = trade_details
        fill_details = self.calc_position_size_in_k(capital)
        self.position_sz = fill_details[0]
        self.true_stop_pips = fill_details[1]
        self.pip_value = 0.1
        self.pnl = 0

    '''Assumption: price has no spread. Usage: to use potion size we say that if position size
    of 50k is worked out then for each pip move we make/lose 5 or 50*0.1'''
    def calc_position_size_in_k(self, capital,trade_friction_func = lambda x : x):
        friction_pips = trade_friction_func(self.trade_details.stop_pips)
        position_size_in_k = (capital * self.trade_details.risk) / (friction_pips * self.pip_value)
        return (round(position_size_in_k, 0), friction_pips)

    @abstractmethod
    def no_friction(self,x):
        return x

def get_currency_dataframe(cur):
    return qdl.get('BOE/' + cur)


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
    return (previous_day_df - df) / previous_day_df


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


def optimize_portfolio(rel_returns_df):
    '''https://wakari.io/sharing/bundle/Pandas4Finance/09_Portfolios?has_login=False'''
    rows, cols = rel_returns_df.shape
    init_guess = pd.DataFrame(np.random.rand(rows, cols), columns=rel_returns_df.columns, index=rel_returns_df.index)
    init_guess = init_guess.divide(init_guess.sum(axis=1), axis=0)
    returns = init_guess * rel_returns_df


def calc_expected_prc_pos(risk, max_rank, x,risk_boundary = 4):
    x_invert =  x - (max_rank + 1)
    if 0 < x < risk_boundary :
        return risk / x
    elif x_invert > -risk_boundary < 0:
        return  risk / x_invert
    else:
        return 0.0

def get_currency_pair_tuple(pair) :
    return (pair[0:3], pair[3:6])

def check_not_conventional(contra, conventions) :
    return [x for x in conventions if get_currency_pair_tuple(x)[0] == contra]

def convert_to_natural_pair(original_pairs_array,benchmarked_ser) :
    benchmark_cur,contra_cur =  get_currency_pair_tuple(benchmarked_ser.name)
    is_unnatural = check_not_conventional(contra_cur, original_pairs_array)
    if is_unnatural :
        actual_name = contra_cur + benchmark_cur
        natural_ser = -benchmarked_ser
        natural_ser.rename(actual_name)
        return natural_ser
    else :
        return benchmarked_ser


def convert_to_natural_pair_df(original_pairs_array, df) :
    conventional_df = df.apply(lambda x : convert_to_natural_pair(original_pairs_array,x))
    new_cols = []
    for x in conventional_df.columns.values :
        benchmark_cur, contra_cur = get_currency_pair_tuple(x)
        if(check_not_conventional(contra_cur, original_pairs_array)) :
            new_cols.append(contra_cur+benchmark_cur)
        else :
            new_cols.append(x)
    conventional_df.columns = new_cols

    return conventional_df

def calc_real_risk(p,p_minus1,current_r,expected_r, max_r):
    max_r_multiplier = max_r * 100
    polarity = -1 if expected_r < 0 else 1
    real_max_r = max_r_multiplier * expected_r
    if (p > p_minus1 and expected_r > 0) or (p < p_minus1 and expected_r < 0) :
        risk = (current_r + expected_r)
        return min(abs(risk),abs(real_max_r)) * polarity
    elif (expected_r == 0) :
        return 0
    else :
        return min(abs(current_r),abs(real_max_r)) * polarity

def calc_rolling_risk(price_df, theoretical_r_df, max_r) :
    rows, cols = price_df.shape
    currencies = price_df.columns.values
    rolling_risk_df = theoretical_r_df.copy()
    for currency in currencies:
        p_ser = price_df[currency]
        r_ser = rolling_risk_df[currency]
        for x in range(1,rows) :
            expected_r = r_ser[x]
            r_ser[x] = calc_real_risk(p_ser[x],p_ser[x - 1],r_ser[x - 1],expected_r, max_r)
    return rolling_risk_df

def calc_avg_closing_range(data_df , periods, avging_periods):
    return (data_df.rolling(window=periods).max() - data_df.rolling(window=periods).min()).rolling(window=avging_periods).mean()

def calc_stop_prices(risk_df,price_df, short_avg_period = 7) :
    avg_range = calc_avg_closing_range(price_df,periods=short_avg_period,avging_periods=28) / 2
    stop_pips_df = avg_range.apply(lambda x: get_pips(x))
    pip_mult_ar = [100 if get_currency_pair_tuple(x)[1] == 'JPY' else 10000 for x in price_df.columns.values]
    stop_as_price_df = (stop_pips_df / pip_mult_ar) * (risk_df.apply(lambda x : np.sign(x)))
    #stop_as_price_df.fillna(value=0, inplace=True)
    return price_df - stop_as_price_df

def get_pips(ser) :
    trade,contra = get_currency_pair_tuple(ser.name)
    if(contra == 'JPY') :
        return ser * 100
    else:
        return ser * 10000

def price_data_to_trade_lines(price_df,rolling_risk_df,stop_df,pips_df):
    trade_details_df = pd.DataFrame(index=price_df.index.values, columns=price_df.columns.values)
    for i in trade_details_df.index.values :
        for c in trade_details_df.columns.values :
            td = TradeLine(price=price_df.ix[i,c],stop=stop_df.ix[i,c],stop_pips= pips_df.ix[i,c],risk=rolling_risk_df.ix[i,c],currency=c,trade_date=i)
            trade_details_df.set_value(i,c,td)
    return trade_details_df

def close_out_trades(portfolio,today) :
    closed_positions = []
    for x in portfolio :
        is_long = x.trade_details.risk > 0
        if is_long and today.price < x.trade_details.stop_price\
                or not is_long and today.price > x.trade_details.stop_price :
            abs_pos = abs(x.position_sz)
            x.pnl = -(x.pip_value * abs_pos * x.true_stop_pips)
            portfolio.remove(x)
            closed_positions.append(x)

    return (portfolio,sum([s.pnl for s in closed_positions]))

def walk_forward(portfolio_capital_tpl, today) :
    new_portfolio = close_out_trades(portfolio_capital_tpl[0],today)
    new_capital = new_portfolio[1] + portfolio_capital_tpl[1]
    for trade_line in today.values :
        if trade_line.risk != 0:
            new_portfolio.append(PnLLine(trade_line,new_capital))
    return (new_portfolio,new_capital)

def backtest(capital, trade_details_df) :
    backtest_results_df = pd.DataFrame(index= trade_details_df.index.values, columns=trade_details_df.columns.values)
    last_t = trade_details_df.index.values[0]
    running_portfolio_capital = ([],capital)
    for t in trade_details_df.index.values[1:] :
        todays_t = walk_forward(portfolio_capital_tpl=running_portfolio_capital, today= trade_details_df.ix[t])
        backtest_results_df.set_value(t,'Portfolio',todays_t[0])
        backtest_results_df.set_value(t, 'PnL', todays_t[1])
        running_portfolio_capital = todays_t
        last_t = todays_t
    return backtest_results_df


def run_algo(periods = 14, risk_per_trade = 0.01,max_risk = 0.05):
    holder = type('', (), {})()
    holder.data_df = FREDDataProvider().get_rates()
    rows, cols = holder.data_df.shape

    holder.relative_returns_df = get_relative_returns(holder.data_df)
    holder.rolling_rel_df = get_rolling_weighted_returns(holder.relative_returns_df, periods=periods)
    holder.ranked_rolling_df = holder.rolling_rel_df.rank(axis=1)
    holder.ranked_rolling_df.fillna(0,inplace=True)
    holder.theoretical_risk = holder.ranked_rolling_df.apply(lambda x: x.apply(lambda y: calc_expected_prc_pos(risk_per_trade, cols, y)))
    holder.conventional_t_risk = convert_to_natural_pair_df(holder.data_df.columns.values,holder.theoretical_risk)
    holder.rolling_risk = calc_rolling_risk(holder.data_df,holder.conventional_t_risk,max_risk)
    holder.stop_price_df = calc_stop_prices(holder.rolling_risk,holder.data_df)
    holder.stop_pips_df = (holder.stop_price_df - holder.data_df).apply(get_pips).fillna(value=0)
    daily_risk = holder.rolling_risk - holder.rolling_risk.shift(1)
    holder.trade_details = price_data_to_trade_lines(holder.data_df, daily_risk, holder.stop_price_df, holder.stop_pips_df)
    return holder


if __name__ == "__main__":
    h = run_algo()
    pnl1 = PnLLine(h.trade_details.ix[-1,-2],10000)


