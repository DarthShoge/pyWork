from lab.strategy.strategy import Strategy
import matplotlib.pyplot as plt
import numpy as np
from lab.core.structures import TradeInstruction
import pandas as pd
# import scipy
import statsmodels.api as sm


class LineReg_Tf(Strategy):
    def __init__(self, lookback):
        self.lookback = lookback

    def schedule(self, positions, data_ser):
        mean = data_ser[-self.lookback].mean()
        # Stop loss percentage is the return over the lookback period
        stoploss = abs(positions[0] * context.lookback / 252) + 1  # percent change per period


    def run(self, rates):
        instructions = pd.DataFrame(None, rates.index, rates.columns, type(TradeInstruction))
        pass

    def get_regressions(self, rates_ser):
        instructions = pd.Series(None, rates_ser.index, TradeInstruction, rates_ser.name)
        rates_window = rates_ser[self.lookback:].rolling(1)
        for i in range(self.lookback, len(rates_ser) - self.lookback):
            window_ser = rates_ser[i - self.lookback:i]
            regr = self.regression(window_ser, instructions[:i - 1])
            new_instruction = TradeInstruction(rates_ser[i], regr[1], regr[0], rates_ser.name, window_ser.index[i])

    def regression(self, data_ser, instructions_ser):
        prices = data_ser.apply(lambda x: x.open)
        days_in_year = 252
        X = range(len(prices))
        A = sm.add_constant(X)
        sd = prices.std()
        Y = prices.values
        profittake = 1.96
        # Run regression y = ax + b
        results = sm.OLS(Y, A).fit()
        (b, a) = results.params
        # Normalized slope
        slope = (a / b) * days_in_year  # Daily return regression * 1 year
        # Currently how far away from regression line?
        delta = Y - (np.dot(a, X) + b)
        # Don't trade if the slope is near flat
        slope_min = 0.252
        # Current gain if trading
        new_weight = np.NaN
        stop_price = np.NaN
        current_position = instructions_ser.apply(lambda x: x.risk).sum()
        s = 'EURGBP'
        # Long but slope turns down, then exit or Short but slope turns upward, then exit
        if (current_position > 0 and slope < 0) or (current_position < 0 and 0 < slope):
            new_weight = -current_position

        # Trend is up
        if slope > slope_min:
            # Price crosses the regression line
            if delta[-1] > 0 and delta[-2] < 0 and current_position == 0:
                stop_price = None
                new_weight = slope
            # Profit take, reaches the top of 95% bollinger band
            if delta[-1] > profittake * sd and current_position > 0:
                new_weight = -current_position

        # Trend is down
        if slope < -slope_min:
            # Price crosses the regression line
            if delta[-1] < 0 and delta[-2] > 0 and current_position == 0:
                stop_price = None
                new_weight = slope

            # Profit take, reaches the top of 95% bollinger band
            if delta[-1] < - profittake * sd and current_position < 0:
                new_weight = -current_position

        return (new_weight, stop_price, b, a, slope)

    # def regression(self, X_len, data, context=None):
    #     prices = data.apply(lambda x: x.open)
    #     X = range(len(prices))
    #     A = sm.add_constant(X)
    #     sd = prices.std()
    #     Y = prices.values
    #     # Run regression y = ax + b
    #     results = sm.OLS(Y, A).fit()
    #     (b, a) = results.params
    #     slope = a / b * X_len
    #     # Currently how far away from regression line?
    #     delta = Y - (np.dot(a, X) + b)
    #     # Don't trade if the slope is near flat
    #     slope_min = 0.252
    #     # Current gain if trading
    #     s = 'EURGBP'
    #     gain = 0  # get_gain(context, s) * 100
    #     if (context.weights[s] > 0 and slope < 0) or (context.weights[s] < 0 and 0 < slope):
    #         context.weights[s] = 0
    #         # Trend is up
    #     if slope > slope_min:
    #         # Price crosses the regression line
    #         if delta[-1] > 0 and delta[-2] < 0 and context.weights[s] == 0:
    #             context.stopprice[s] = None
    #             context.weights[s] = slope
    #         # Profit take, reaches the top of 95% bollinger band
    #         if delta[-1] > context.profittake * sd and context.weights[s] > 0:
    #             context.weights[s] = 0
    #     # Trend is down
    #
    #     if slope < -slope_min:
    #         # Price crosses the regression line
    #         if delta[-1] < 0 and delta[-2] > 0 and context.weights[s] == 0:
    #             context.stopprice[s] = None
    #             context.weights[s] = slope
    #
    #         # Profit take, reaches the top of 95% bollinger band
    #         if delta[-1] < - context.profittake * sd and context.weights[s] < 0:
    #             context.weights[s] = 0
    #
    #     return (b, a, slope)

    def plot_regr(a, b, X, Y):
        Y_reg = np.dot(a, X) + b
        plt.plot(X, Y_reg, '.')
        plt.plot(X, Y, '-')
