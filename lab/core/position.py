from lab.core.structures import Direction, StopType
from lab.core.transaction import Transaction
from lab.core.pnl_line import PnlLine
from lab.core.common import as_price


class Position:
    def __init__(self, initiating_line, capital, commission_per_k=0.0, spread=0.0):
        if initiating_line.risk == 0:
            raise LookupError('cannot initiate holding with no risk')

        trsction = Transaction(initiating_line, capital, commission_per_k=commission_per_k, spread=spread)
        self.lines = [trsction]
        self.commission_per_k = commission_per_k
        self.spread = spread
        self.pnl_history = [0]
        self.transaction_pnls = []
        self.currency = initiating_line.currency

    @property
    def net_direction(self):
        return None if not self.lines else self.lines[-1].direction

    @property
    def net_risk(self):
        return 0 if not self.lines else sum([l.risk for l in self.lines])

    @property
    def summary_pnl(self):
        return PnlLine.sum([x for x in self.transaction_pnls])

    def close_stop_outs(self, candle):
        running_pnl = 0
        for line in self.lines:
            if line.trade_details.stop_type is StopType.Soft:
                continue
            spread_price = as_price(line.spread, line.trade_details.currency)
            short_stopped_out = line.direction is Direction.Short and candle.high + spread_price >= line.trade_details.stop
            long_stopped_out = line.direction is Direction.Long and candle.low - spread_price <= line.trade_details.stop
            if short_stopped_out or long_stopped_out:
                running_pnl += line.close_transaction(line.trade_details.stop, date=candle.date) #maybe we should use spread + price here
                self.close_transaction(line)
        return running_pnl

    def revalue_position(self, trade_line, current_candle, current_capital):

        if trade_line.currency != self.currency:
            raise LookupError('Currencies do not match')

        pnl_line = Transaction(trade_line, current_capital, commission_per_k=self.commission_per_k, spread=self.spread)
        locked_in_pnl = 0
        locked_in_pnl += self.close_stop_outs(current_candle)

        if abs(pnl_line.risk) > 0 and (self.net_direction is None or self.net_direction == pnl_line.direction):
            locked_in_pnl += pnl_line.pnl
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
                            locked_in_pnl += line.close_transaction(price=trade_line.price,date=trade_line.trade_date)
                            self.close_transaction(line)
                        else:
                            locked_in_pnl += line.close_transaction(trade_line.price, residual_risk, trade_line.trade_date)
                            if line.risk == 0:
                                self.close_transaction(line)
                            residual_risk = 0

        self.pnl_history.append(locked_in_pnl)
        return locked_in_pnl

    def close_transaction(self, line):
        self.lines.remove(line)
        self.transaction_pnls.append(line.summary_pnl)