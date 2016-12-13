import unittest
from lab import PnlLine, ExitType, TradeInstruction
import datetime as dt


class PnlLineUnitTests(unittest.TestCase):

    def test_add_pnl_lines_should_sum_on_add_pnl_fields(self):
        t = TradeInstruction(currency="EURUSD", price=1.1000, stop=1.0090, risk=0.01, trade_date=dt.date(2014, 10, 10))
        to_date = dt.date(2014, 10, 20)
        t2 = TradeInstruction(currency="EURUSD", price=1.1100, stop=1.1050, risk=0.01, trade_date=to_date)
        close_price = 1.110
        pnl1 = PnlLine(opening_trade=t, close_price=close_price, pnl=1000, to_date=to_date)
        pnl2 = PnlLine(opening_trade=t2, close_price=1200, pnl=1000, to_date=to_date + dt.timedelta(days=15))
        result = pnl1 + pnl2
        self.assertAlmostEqual(result.pnl, pnl1.pnl + pnl2.pnl)

    def test_add_pnl_lines_should_use_earliest_from_date_in_product(self):
        trade_date = dt.date(2014, 10, 10)
        t = TradeInstruction(currency="EURUSD", price=1.1000, stop=1.0090, risk=0.01, trade_date=trade_date)
        to_date = trade_date + dt.timedelta(days=15)
        t2 = TradeInstruction(currency="EURUSD", price=1.1100, stop=1.1050, risk=0.01, trade_date=to_date)
        close_price = 1.110
        pnl1 = PnlLine(opening_trade=t, close_price=close_price, pnl=1000, to_date=to_date)
        pnl2 = PnlLine(opening_trade=t2, close_price=1200, pnl=1000, to_date=to_date + dt.timedelta(days=15))
        result = pnl1 + pnl2
        result2 = pnl2 + pnl1
        self.assertEqual(trade_date, result.from_date)
        self.assertEqual(trade_date, result2.from_date)

    def test_add_pnl_lines_should_use_latest_to_date_in_product(self):
        trade_date = dt.date(2014, 10, 10)
        t = TradeInstruction(currency="EURUSD", price=1.1000, stop=1.0090, risk=0.01, trade_date=trade_date)
        to_date = trade_date + dt.timedelta(days=15)
        t2 = TradeInstruction(currency="EURUSD", price=1.1100, stop=1.1050, risk=0.01, trade_date=to_date)
        close_price = 1.110
        pnl1 = PnlLine(opening_trade=t, close_price=close_price, pnl=1000, to_date=to_date)
        to_date2 = to_date + dt.timedelta(days=15)
        pnl2 = PnlLine(opening_trade=t2, close_price=1200, pnl=1000, to_date=to_date2)
        result = pnl1 + pnl2
        result2 = pnl2 + pnl1
        self.assertEqual(to_date2, result.to_date)
        self.assertEqual(to_date2, result2.to_date)

    def test_add_pnl_lines_should_use_opening_price_from_earliest_trade_in_product(self):
        earliest_open = 1.1000
        t = TradeInstruction(currency="EURUSD", price=earliest_open, stop=1.0090, risk=0.01, trade_date=dt.date(2014, 10, 10))
        to_date = t.trade_date + dt.timedelta(days=15)
        t2 = TradeInstruction(currency="EURUSD", price=1.1100, stop=1.1050, risk=0.01, trade_date=to_date)
        close_price = 1.110
        pnl1 = PnlLine(opening_trade=t, close_price=close_price, pnl=1000, to_date=to_date)
        pnl2 = PnlLine(opening_trade=t2, close_price=1200, pnl=1000, to_date=to_date + dt.timedelta(days=15))
        result = pnl1 + pnl2
        result2 = pnl2 + pnl1
        self.assertEqual(earliest_open, result.open_price)
        self.assertEqual(earliest_open, result2.open_price)

    def test_add_pnl_lines_should_use_closing_price_from_latest_trade_in_product(self):
        t = TradeInstruction(currency="EURUSD", price=1.1000, stop=1.0090, risk=0.01,
                             trade_date=dt.date(2014, 10, 10))
        to_date = t.trade_date + dt.timedelta(days=15)
        t2 = TradeInstruction(currency="EURUSD", price=1.1100, stop=1.1050, risk=0.01, trade_date=to_date)
        close_price = 1.110
        pnl1 = PnlLine(opening_trade=t, close_price=close_price, pnl=1000, to_date=to_date)
        pnl2 = PnlLine(opening_trade=t2, close_price=1200, pnl=1000, to_date=to_date + dt.timedelta(days=15))
        result = pnl1 + pnl2
        result2 = pnl2 + pnl1
        self.assertEqual(pnl2.close_price, result.close_price)
        self.assertEqual(pnl2.close_price, result2.close_price)

    def test_add_pnl_lines_should_throw_if_currencies_are_different(self):
        t = TradeInstruction(currency="EURUSD", price=1.1000, stop=1.0090, risk=0.01, trade_date=dt.date(2014, 10, 10))
        to_date = dt.date(2014, 10, 20)
        t2 = TradeInstruction(currency="GBPUSD", price=1.1100, stop=1.1050, risk=0.01, trade_date=to_date)
        close_price = 1.110
        pnl1 = PnlLine(opening_trade=t, close_price=close_price, pnl=1000, to_date=to_date)
        pnl2 = PnlLine(opening_trade=t2, close_price=1200, pnl=1000, to_date=to_date + dt.timedelta(days=15))
        with self.assertRaises(LookupError):
            pnl1 + pnl2

    def test_add_pnl_lines_should_have_mixed_exit_type_if_multiple_exit_types(self):
        t = TradeInstruction(currency="EURUSD", price=1.1000, stop=1.0090, risk=0.01, trade_date=dt.date(2014, 10, 10))
        to_date = dt.date(2014, 10, 20)
        t2 = TradeInstruction(currency="EURUSD", price=1.1100, stop=1.1050, risk=0.01, trade_date=to_date)
        close_price = 1.110
        pnl1 = PnlLine(opening_trade=t, close_price=close_price, pnl=1000, to_date=to_date)
        pnl2 = PnlLine(opening_trade=t2, close_price=1200, pnl=-1000, to_date=to_date + dt.timedelta(days=15))
        pnl2.exit_type = ExitType.Stopped
        result = pnl1 + pnl2
        self.assertEqual(ExitType.Multi, result.exit_type)

    def test_add_pnl_lines_should_have_closed_exit_type_if_both_were_closed(self):
        t = TradeInstruction(currency="EURUSD", price=1.1000, stop=1.0090, risk=0.01, trade_date=dt.date(2014, 10, 10))
        to_date = dt.date(2014, 10, 20)
        t2 = TradeInstruction(currency="EURUSD", price=1.1100, stop=1.1050, risk=0.01, trade_date=to_date)
        close_price = 1.110
        pnl1 = PnlLine(opening_trade=t, close_price=close_price, pnl=1000, to_date=to_date)
        pnl2 = PnlLine(opening_trade=t2, close_price=1200, pnl=-1000, to_date=to_date + dt.timedelta(days=15))
        pnl1.exit_type = ExitType.Closed
        pnl2.exit_type = ExitType.Closed
        result = pnl1 + pnl2
        self.assertEqual(ExitType.Closed, result.exit_type)

    def test_add_pnl_lines_should_have_stopped_exit_type_if_both_were_stopped(self):
        t = TradeInstruction(currency="EURUSD", price=1.1000, stop=1.0090, risk=0.01, trade_date=dt.date(2014, 10, 10))
        to_date = dt.date(2014, 10, 20)
        t2 = TradeInstruction(currency="EURUSD", price=1.1100, stop=1.1050, risk=0.01, trade_date=to_date)
        close_price = 1.110
        pnl1 = PnlLine(opening_trade=t, close_price=close_price, pnl=1000, to_date=to_date)
        pnl2 = PnlLine(opening_trade=t2, close_price=1200, pnl=-1000, to_date=to_date + dt.timedelta(days=15))
        pnl1.exit_type = ExitType.Stopped
        pnl2.exit_type = ExitType.Stopped
        result = pnl1 + pnl2
        self.assertEqual(ExitType.Stopped, result.exit_type)

    def test_add_pnl_lines_should_sum_properly(self):
        t = TradeInstruction(currency="EURUSD", price=1.1000, stop=1.0090, risk=0.01, trade_date=dt.date(2014, 10, 10))
        to_date = dt.date(2014, 10, 20)
        t2 = TradeInstruction(currency="EURUSD", price=1.1100, stop=1.1050, risk=0.01, trade_date=to_date)
        close_price = 1.110
        pnl1 = PnlLine(opening_trade=t, close_price=close_price, pnl=1000, to_date=to_date)
        pnl2 = PnlLine(opening_trade=t2, close_price=1200, pnl=-750, to_date=to_date + dt.timedelta(days=15))
        pnl3 = PnlLine(opening_trade=t2, close_price=1200, pnl=4000, to_date=to_date + dt.timedelta(days=25))
        pnl4 = PnlLine(opening_trade=t2, close_price=1200, pnl=-250, to_date=to_date + dt.timedelta(days=30))
        result = PnlLine.sum([pnl1,pnl2,pnl3,pnl4])
        self.assertAlmostEqual(result.pnl, 4000)
        self.assertEqual(pnl4.to_date, result.to_date)
        self.assertEqual(pnl1.from_date, result.from_date)

    def test_sum_pnl_lines_should_return_none_on_empty_list(self):
        result = PnlLine.sum([])
        self.assertEqual(result, None)

    def test_sum_pnl_lines_should_sum_single_line_properly(self):
        t = TradeInstruction(currency="EURUSD", price=1.1000, stop=1.0090, risk=0.01, trade_date=dt.date(2014, 10, 10))
        to_date = dt.date(2014, 10, 20)
        pnl1 = PnlLine(opening_trade=t, close_price=1.2, pnl=1000, to_date=to_date)
        result = PnlLine.sum([pnl1])
        self.assertEqual(result, pnl1)
