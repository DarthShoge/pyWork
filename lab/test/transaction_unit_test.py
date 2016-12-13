import datetime as dt
import unittest

from lab import Transaction, InitError,PnlLine,ExitType
from lab.core.structures import Direction, TradeInstruction


class TransactionUnitTests(unittest.TestCase):

    def test_transaction_constructor_with_no_trade_details_should_throw(self):
        with self.assertRaises(Exception) :
            Transaction(trade_details=None,capital=2500)

    def test_transaction_constructor_sets_short_direction_correctly_when_risk_is_negative(self):
        trade_details = TradeInstruction(1.500, 1.550, -0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details,10000)
        self.assertEqual(Direction.Short,tran.direction)

    def test_transaction_constructor_sets_long_direction_correctly_when_risk_is_positive(self):
        trade_details = TradeInstruction(1.500, 1.450, 0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, 10000)
        self.assertEqual(Direction.Long,tran.direction)

    def test_transaction_constructor_validates_that_stop_is_in_opposite_direction(self):
        trade_details = TradeInstruction(1.500, 1.550, 0.01, 'USDGBP', dt.date)
        with self.assertRaises(InitError):
            Transaction(trade_details, 10000)

    def test_transaction_constructor_sets_initial_pnl_to_0(self):
        trade_details = TradeInstruction(1.500, 1.450, 0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, 10000)
        self.assertEqual(0,tran.pnl)

    def test_transaction_constructor_sets_position_sz_in_k_properly_for_long_positive_capital(self):
        trade_details = TradeInstruction(1.500, 1.4950, 0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, 10000)
        self.assertEqual(20,tran.position_sz)

    def test_transaction_constructor_sets_position_sz_in_k_properly_for_short_positive_capital(self):
        trade_details = TradeInstruction(1.500, 1.5050, -0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, 10000)
        self.assertEqual(-20, tran.position_sz)

    def test_transaction_constructor_sets_position_sz_in_k_properly_for_long_0_capital(self):
        trade_details = TradeInstruction(1.500, 1.450, 0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, 0)
        self.assertEqual(0,tran.position_sz)

    def test_transaction_constructor_sets_position_sz_in_k_to_0_for_long_negative_capital(self):
        trade_details = TradeInstruction(1.500, 1.450, 0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, -1000)
        self.assertEqual(0,tran.position_sz)

    def test_transaction_constructor_sets_position_sz_in_k_to_0_for_short_negative_capital(self):
        trade_details = TradeInstruction(1.500, 1.550, -0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, -1000)
        self.assertEqual(0,tran.position_sz)

    def test_transaction_constructor_sets_position_sz_in_k_to_0_if_stop_and_price_are_same(self):
        trade_details = TradeInstruction(1.500, 1.500, -0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, 10000)
        self.assertEqual(0,tran.position_sz)

    def test_transaction_get_value_since_last_observation_calculates_difference_on_positive_long_move_without_delta(self):
        trade_details = TradeInstruction(1.500, 1.4950, 0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, 10000)
        result = tran.value_since_last_observation(1.6)
        self.assertAlmostEquals(20.0*(1000*0.1), result,5)

    def test_transaction_get_value_since_last_observation_calculates_difference_on_positive_short_move_without_delta(self):
        trade_details = TradeInstruction(1.5000, 1.5050, -0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, 10000)
        result = tran.value_since_last_observation(1.4950)
        self.assertAlmostEquals(20.0*(50*0.1), result)

    def test_transaction_get_value_since_last_observation_calculates_difference_on_negative_short_move_with_delta(self):
        trade_details = TradeInstruction(1.500, 1.550, -0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, 10000)
        result = tran.value_since_last_observation(1.550,1.500)
        self.assertAlmostEquals(-100, result)

    def test_transaction_get_value_since_last_observation_calculates_difference_on_positive_long_move_with_delta(self):
        trade_details = TradeInstruction(1.500, 1.4950, 0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, 10000)
        result = tran.value_since_last_observation(1.4950,1.5)
        self.assertAlmostEquals(-100, result,5)

    def test_transaction_get_value_since_last_observation_calculates_difference_on_negative_short_move_with_pos_nom(self):
        trade_details = TradeInstruction(1.500, 1.550, -0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, 10000)
        result = tran.value_since_last_observation(1.550,1.500,-10)
        self.assertAlmostEquals(-500, result)

    def test_transaction_get_value_since_last_observation_calculates_difference_on_positive_long_move_with_pos_nom(self):
        trade_details = TradeInstruction(1.500, 1.4950, 0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, 10000)
        result = tran.value_since_last_observation(1.4950,1.5,10)
        self.assertAlmostEquals(-50, result,5)

    def test_transaction_get_value_since_last_observation_calculates_difference_on_no_change(self):
        trade_details = TradeInstruction(1.500, 1.4950, 0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, 10000)
        result = tran.value_since_last_observation(1.500)
        self.assertAlmostEquals(0, result,5)

    def test_transaction_close_out_should_full_with_0_pnl_on_no_move(self):
        trade_details = TradeInstruction(1.500, 1.4950, 0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, 10000)
        result = tran.close_transaction(1.500)
        self.assertAlmostEquals(0, tran.pnl)

    def test_transaction_close_out_should_fully_close_out_with_0_pnl_on_no_move(self):
        trade_details = TradeInstruction(1.500, 1.4950, 0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, 10000)
        result = tran.close_transaction(1.5050)
        self.assertAlmostEquals(100, tran.pnl)

    def test_transaction_close_out_should_fully_close_out_risk_on_no_move(self):
        trade_details = TradeInstruction(1.500, 1.4950, 0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, 10000)
        result = tran.close_transaction(1.5050)
        self.assertAlmostEquals(0, tran.risk)

    def test_transaction_close_out_should_throw_if_trying_to_close_out_in_direction_of_the_trade_for_long(self):
        trade_details = TradeInstruction(1.500, 1.4950, 0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, 10000)
        with self.assertRaises(RuntimeError) as ex :
            tran.close_transaction(1.5050,0.05)

    def test_transaction_close_out_should_throw_if_trying_to_close_out_in_direction_of_the_trade_for_short(self):
        trade_details = TradeInstruction(1.500, 1.550, -0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, 10000)
        with self.assertRaises(RuntimeError) as ex :
            tran.close_transaction(1.4950,-0.05)

    def test_transaction_close_out_partial_should_correctly_calculate_pnl_for_long(self):
        trade_details = TradeInstruction(1.500, 1.4950, 0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, 10000)
        result = tran.close_transaction(1.5050,-0.005)
        self.assertAlmostEqual(50,result)
        self.assertAlmostEqual(50, tran.pnl)

    def test_transaction_close_out_partial_should_correctly_calculate_pnl_for_short(self):
        trade_details = TradeInstruction(1.500, 1.5050, -0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, 10000)
        result = tran.close_transaction(1.4950,0.005)
        self.assertAlmostEqual(50,result)
        self.assertAlmostEqual(50, tran.pnl)

    def test_transaction_close_out_partial_should_correctly_change_residual_risk_for_long(self):
        trade_details = TradeInstruction(1.500, 1.4950, 0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, 10000)
        result = tran.close_transaction(1.5050,-0.005)
        self.assertAlmostEqual(0.005, tran.risk)


    def test_transaction_close_out_partial_should_correctly_change_residual_risk_for_short(self):
        trade_details = TradeInstruction(1.500, 1.5050, -0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, 10000)
        result = tran.close_transaction(1.4950,0.005)
        self.assertAlmostEqual(-0.005, tran.risk)

    def test_transaction_close_out_partial_should_only_close_up_to_full_risk_for_long(self):
        trade_details = TradeInstruction(1.500, 1.4950, 0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, 10000)
        with self.assertRaises(RuntimeError) :
            tran.close_transaction(1.5050,-0.02)

    def test_transaction_close_out_partial_should_correctly_calculate_pnl_for_short(self):
        trade_details = TradeInstruction(1.500, 1.5050, -0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, 10000)
        with self.assertRaises(RuntimeError):
            tran.close_transaction(1.4950, 0.02)

    def test_transaction_transaction_cost_is_applied_on_close_for_short(self):
        trade_details = TradeInstruction(1.500, 1.5050, -0.01, 'USDGBP', dt.date)
        commission_cost = 0.06
        tran = Transaction(trade_details, 10000, commission_per_k=commission_cost)
        expected_result = 100 - (commission_cost * abs(tran.position_sz) * 2)
        tran.close_transaction(1.4950)
        self.assertAlmostEqual(expected_result, sum(tran.historic_pnl))

    def test_transaction_transaction_cost_is_applied_on_close_for_long(self):
        trade_details = TradeInstruction(1.500, 1.4950, 0.01, 'USDGBP', dt.date)
        commission_cost = 0.06
        tran = Transaction(trade_details, 10000, commission_per_k=commission_cost)
        expected_result = 100 - (commission_cost * abs(tran.position_sz) * 2)
        tran.close_transaction(1.5050)
        self.assertAlmostEqual(expected_result, sum(tran.historic_pnl))

    def test_transaction_transaction_cost_is_applied_correct_amount_of_times(self):
        trade_details = TradeInstruction(1.500, 1.4950, 0.01, 'USDGBP', dt.date)
        commission_cost = 0.06
        tran = Transaction(trade_details, 10000, commission_per_k=commission_cost)
        expected_result = 100 - (commission_cost * abs(tran.position_sz) * 2)
        tran.close_transaction(1.5050,-0.005)
        tran.close_transaction(1.5050,-0.005)
        self.assertAlmostEqual(expected_result, sum(tran.historic_pnl))

    def test_transaction_spread_should_add_in_pips_to_exit_price_for_long(self):
        trade_details = TradeInstruction(1.500, 1.4950, 0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, 10000, spread=2.0)
        result = tran.close_transaction(1.5050)
        self.assertAlmostEquals(92, sum(tran.historic_pnl))

    def test_transaction_spread_should_remove_in_pips_to_exit_price_for_short(self):
        trade_details = TradeInstruction(1.500, 1.5050, -0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, 10000, spread=2.0)
        result = tran.close_transaction(1.4950)
        self.assertAlmostEquals(92, sum(tran.historic_pnl))

    def test_transaction_spread_should_not_affect_position_size(self):
        trade_details = TradeInstruction(1.500, 1.4950, 0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, 10000, spread=2.0)
        self.assertAlmostEquals(20, tran.position_sz)

    def test_transaction_spread_should_be_applied_on_both_entry_and_exit(self):
        trade_details = TradeInstruction(1.5000, 1.5050, -0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, 10000, spread=2.0)
        result = tran.close_transaction(1.5000)
        self.assertAlmostEquals(-8.00, sum(tran.historic_pnl))

    def test__when_transaction_value_is_intitialised_statistic_pnl_line_should_properly_init(self):
        trade_details = TradeInstruction(1.500, 1.5050, -0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, 10000)
        self.assertEqual(trade_details.trade_date, tran.statistic_pnl.from_date)
        self.assertEqual(trade_details.currency, tran.statistic_pnl.currency)
        self.assertEqual(trade_details.price, tran.statistic_pnl.open_price)

    def test__when_transaction_closed_statistic_pnl_line_should_set_correct_exit_type_on_close(self):
        trade_details = TradeInstruction(1.500, 1.5050, -0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, 10000)
        result = tran.close_transaction(1.4950)
        self.assertAlmostEqual(100, result)
        self.assertEqual(ExitType.Closed, tran.statistic_pnl.exit_type)

    def test__when_transaction_closed_statistic_pnl_line_should_set_correct_date(self):
        trade_details = TradeInstruction(1.500, 1.5050, -0.01, 'USDGBP', dt.date(2015, 1, 1))
        tran = Transaction(trade_details, 10000)
        end_date = dt.date(2015, 10, 1)
        result = tran.close_transaction(price=1.4950, date=end_date)
        self.assertAlmostEqual(end_date, tran.statistic_pnl.to_date)

    def test__when_transaction_closed_statistic_pnl_line_should_set_correct_date(self):
        trade_details = TradeInstruction(1.500, 1.5050, -0.01, 'USDGBP', dt.date(2015, 1, 1))
        tran = Transaction(trade_details, 10000)
        end_date = dt.date(2015, 10, 1)
        result = tran.close_transaction(price=1.4950, date=end_date)
        self.assertAlmostEqual(end_date, tran.statistic_pnl.to_date)

    def test__when_transaction_closed_statistic_pnl_line_should_set_correct_pnl_and_close_price(self):
        trade_details = TradeInstruction(1.500, 1.5050, -0.01, 'USDGBP', dt.date(2015, 1, 1))
        tran = Transaction(trade_details, 10000,spread=2.0)
        end_date = dt.date(2015, 10, 1)
        result = tran.close_transaction(price=1.4950, date=end_date)
        self.assertAlmostEqual(sum(tran.historic_pnl), tran.statistic_pnl.pnl)

    def test__when_transaction_closed_statistic_pnl_line_should_set_correct_exit_type_when_stopped_out_on_short(self):
        trade_details = TradeInstruction(1.500, 1.5050, -0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, 10000)
        result = tran.close_transaction(1.5050)
        self.assertAlmostEqual(-100, result)
        self.assertEqual(ExitType.Stopped, tran.statistic_pnl.exit_type)

    def test__when_transaction_closed_statistic_pnl_line_should_set_correct_exit_type_when_stopped_out_on_long(self):
        trade_details = TradeInstruction(1.500, 1.4950, 0.01, 'USDGBP', dt.date)
        tran = Transaction(trade_details, 10000)
        result = tran.close_transaction(1.4950)
        self.assertAlmostEqual(-100, result)
        self.assertEqual(ExitType.Stopped, tran.statistic_pnl.exit_type)



