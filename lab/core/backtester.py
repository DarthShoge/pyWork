import numpy as np
import pandas as pd

from lab import Position, get_range


class Backtester:
    def __init__(self, dataprovider, strategy):
        self.dataprovider = dataprovider
        self.strategy = strategy
        self.position_pnls = []

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