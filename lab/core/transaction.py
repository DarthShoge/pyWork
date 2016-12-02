from abc import abstractmethod

import numpy as np

from lab import InitError, get_pips, as_price
from lab.core.structures import Direction


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