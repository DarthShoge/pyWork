import unittest
import datetime as dt
from lab import *


class PositionUnitTests(unittest.TestCase):
    def create_trade_line(self, price=1.500, stop=1.4950, risk=0.01, currency='USDGBP', date=dt.date):
        return TradeInstruction(price, stop, risk, currency, date)

    def create_transaction(self, price=1.500, stop=1.4950, risk=0.01, currency='USDGBP', date=dt.date, spread=0):
        trade_details = self.create_trade_line(price, stop, risk, currency, date)
        tran = Transaction(trade_details, 10000, spread=spread)
        return tran

    def test_position_with_no_transaction_should_throw(self):
        with self.assertRaises(Exception) as ex:
            Position(initiating_line=None, capital=10000)

    def test_position_with_initial_transaction_should_be_added_to_transaction_lines(self):
        transaction = self.create_transaction()
        position = Position(transaction.trade_details,10000)
        self.assertEqual(transaction.trade_details, position.lines[0].trade_details)

    def test_position_should_set_currency_correctly(self):
        transaction = self.create_transaction(currency="EURUSD")
        position = Position(transaction.trade_details,10000)
        self.assertEqual("EURUSD", position.currency)

    def test_position_should_set_direction_correctly(self):
        transaction = self.create_transaction(currency="EURUSD")
        position = Position(transaction.trade_details, 10000)
        self.assertEqual(Direction.Long, position.net_direction)

    def test_revalue_position_should_not_add_transaction_if_no_risk(self):
        transaction = self.create_transaction(price=1.5,stop=1.5050,risk=-0.01)
        position = Position(transaction.trade_details, 10000)
        trade_instructions = self.create_trade_line(price=1.5005,stop=1.5050,risk=0)
        position.revalue_position(trade_instructions, 10000)
        self.assertEqual(1,position.lines.__len__())

    def test_revalue_position_should_not_add_transaction_if_different_currency(self):
        trade_instruction = self.create_trade_line(currency='EURGBP')
        position = Position(trade_instruction, 10000)
        trade_instruction2 = self.create_trade_line(currency='USDJPY' )
        with self.assertRaises(LookupError) as ex:
            position.revalue_position(trade_instruction2, 10000)

    def test_revalue_position_should_apply_transaction_costs_on_initialisation(self):
        transaction = self.create_transaction(price=1.5,stop=1.5050,risk=-0.01)
        position = Position(transaction.trade_details, 10000, spread=2)
        self.assertEquals(transaction.pnl, position.pnl_history[-1])

    def test_revalue_position_should_return_0_pnl_if_no_close_out(self):
        transaction = self.create_transaction(price=1.5,stop=1.5050,risk=-0.01)
        position = Position(transaction.trade_details, 10000)
        trade_instructions = self.create_trade_line(price=1.4990,stop=1.5050,risk=0)
        position.revalue_position(trade_instructions, 10000)
        self.assertEqual(0, position.pnl_history[-1])

    def test_revalue_position_should_return_0_pnl_if_no_close_out(self):
        transaction = self.create_transaction(price=1.5,stop=1.5050,risk=-0.01)
        position = Position(transaction.trade_details, 10000)
        trade_instructions = self.create_trade_line(price=1.4990,stop=1.5050,risk=0)
        position.revalue_position(trade_instructions, 10000)
        self.assertEqual(0, position.pnl_history[-1])

    def test_revalue_position_should_close_stop_outs_at_loss(self):
        transaction = self.create_transaction(price=1.5,stop=1.5050,risk=-0.01)
        position = Position(transaction.trade_details, 10000)
        trade_instructions = self.create_trade_line(price=1.5051,stop=1.5070,risk=0)
        position.revalue_position(trade_instructions, 10000)
        self.assertAlmostEqual(-100, position.pnl_history[-1])

    def test_revalue_position_should_add_position_if_there_is_risk(self):
        transaction = self.create_transaction(price=1.5,stop=1.5050,risk=-0.01)
        position = Position(transaction.trade_details, 10000)
        trade_instructions = self.create_trade_line(price=1.4990,stop=1.5040,risk=-0.01)
        position.revalue_position(trade_instructions, 10000)
        self.assertEqual(2, position.lines.__len__())

    def test_revalue_position_partial_close_out_should_not_change_amount_of_transactions(self):
        transaction = self.create_transaction(price=1.5,stop=1.5050,risk=-0.01)
        position = Position(transaction.trade_details, 10000)
        trade_instructions = self.create_trade_line(price=1.4990,stop=1.4950,risk=0.005)
        position.revalue_position(trade_instructions, 10000)
        self.assertEqual(1, position.lines.__len__())

    def test_revalue_position_partial_close_out_should_set_residual_risk_correctly(self):
        transaction = self.create_transaction(price=1.5,stop=1.5050,risk=-0.01)
        position = Position(transaction.trade_details, 10000)
        trade_instructions = self.create_trade_line(price=1.4990,stop=1.4950,risk=0.005)
        position.revalue_position(trade_instructions, 10000)
        self.assertAlmostEqual(-0.005, position.lines[0].risk)

    def test_revalue_position_partial_close_out_should_set_pnl_correctly(self):
        transaction = self.create_transaction(price=1.5,stop=1.5050,risk=-0.01)
        position = Position(transaction.trade_details, 10000)
        trade_instructions = self.create_trade_line(price=1.4990,stop=1.4950,risk=0.005)
        position.revalue_position(trade_instructions, 10000)
        self.assertAlmostEqual(10, position.pnl_history[-1])

    def test_revalue_position_partial_close_out_should_set_pnl_correctly_on_multiple_legs(self):
        transaction = self.create_transaction(price=1.5, stop=1.5050, risk=-0.01)
        position = Position(transaction.trade_details, 10000)
        trade_instructions = self.create_trade_line(price=1.4990, stop=1.4950, risk=0.005)
        position.revalue_position(trade_instructions, 10000)
        trade_instructions = self.create_trade_line(price=1.4980, stop=1.4950, risk=0.005)
        position.revalue_position(trade_instructions, 10000)
        self.assertAlmostEqual(20, position.pnl_history[-1])
        self.assertAlmostEqual(30, sum(position.pnl_history))

    def test_revalue_position_partial_close_out_should_remove_transactions_correctly_on_multiple_legs(self):
        transaction = self.create_transaction(price=1.5, stop=1.5050, risk=-0.01)
        position = Position(transaction.trade_details, 10000)
        trade_instructions = self.create_trade_line(price=1.4990, stop=1.4950, risk=0.005)
        position.revalue_position(trade_instructions, 10000)
        trade_instructions = self.create_trade_line(price=1.4980, stop=1.4950, risk=0.005)
        position.revalue_position(trade_instructions, 10000)
        self.assertFalse(position.lines)

    def test_revalue_position_partial_close_out_should_set_correct_pnl_when_position_is_flipped(self):
        transaction = self.create_transaction(price=1.5, stop=1.5050, risk=-0.01)
        position = Position(transaction.trade_details, 10000)
        trade_instructions = self.create_trade_line(price=1.4990, stop=1.4950, risk=0.005)
        position.revalue_position(trade_instructions, 10000)
        trade_instructions = self.create_trade_line(price=1.4980, stop=1.4940, risk=0.01)
        position.revalue_position(trade_instructions, 10000)
        self.assertAlmostEqual(30, sum(position.pnl_history))

    def test_revalue_position_partial_close_out_should_set_correct_net_direction_when_position_is_flipped(self):
        transaction = self.create_transaction(price=1.5, stop=1.5050, risk=-0.01)
        position = Position(transaction.trade_details, 10000)
        trade_instructions = self.create_trade_line(price=1.4990, stop=1.4950, risk=0.005)
        position.revalue_position(trade_instructions, 10000)
        trade_instructions = self.create_trade_line(price=1.4980, stop=1.4940, risk=0.01)
        position.revalue_position(trade_instructions, 10000)
        self.assertEqual(Direction.Long, position.net_direction)

    def test_revalue_position_partial_close_out_should_set_correct_risk_direction_when_position_is_flipped(self):
        transaction = self.create_transaction(price=1.5, stop=1.5050, risk=-0.01)
        position = Position(transaction.trade_details, 10000)
        trade_instructions = self.create_trade_line(price=1.4990, stop=1.4950, risk=0.005)
        position.revalue_position(trade_instructions, 10000)
        trade_instructions = self.create_trade_line(price=1.4980, stop=1.4940, risk=0.01)
        position.revalue_position(trade_instructions, 10000)
        self.assertAlmostEqual(0.005, position.lines[0].risk)




