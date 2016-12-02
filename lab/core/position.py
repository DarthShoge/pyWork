from lab.core.structures import Direction
from lab.core.transaction import Transaction


class Position:
    def __init__(self, initiating_line, capital, commission_per_k=0.0, spread=0.0):
        if initiating_line.risk == 0:
            raise LookupError('cannot initiate holding with no risk')

        trsction = Transaction(initiating_line, capital, commission_per_k=commission_per_k, spread=spread)
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