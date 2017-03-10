import datetime as dt
import unittes
from lab import Ohlc

from lab import Transaction, Position
from lab.core.structures import Direction, TradeInstruction, StopType


def ohcl(o, c, h, l):
    return Ohlc(o, h, l, c, dt.datetime.today())


class PositionUnitTests(unittest.TestCase):
    def create_trade_line(self, price=1.500, stop=1.4950, risk=0.01, currency='USDGBP', date=dt.date, stop_type=StopType.Hard):
        return TradeInstruction(price, stop, risk, currency, date, stop_type)

    def create_transaction(self, price=1.500, stop=1.4950, risk=0.01, currency='USDGBP', date=dt.date, spread=0, stop_type=StopType.Hard):
        trade_details = self.create_trade_line(price, stop, risk, currency, date, stop_type)
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
        instruction = self.create_trade_line(price=1.5005,stop=1.5050,risk=0)
        candle = ohcl(instruction.price,instruction.price, instruction.price, instruction.price)
        position.revalue_position(instruction, candle, 10000)
        self.assertEqual(1,position.lines.__len__())

    def test_revalue_position_should_not_add_transaction_if_different_currency(self):
        trade_instruction = self.create_trade_line(currency='EURGBP')
        position = Position(trade_instruction, 10000)
        instruction2 = self.create_trade_line(currency='USDJPY' )
        candle = ohcl(instruction2.price,instruction2.price, instruction2.price, instruction2.price)
        with self.assertRaises(LookupError) as ex:
            position.revalue_position(instruction2, candle, 10000)

    def test_revalue_position_should_apply_transaction_costs_on_initialisation(self):
        transaction = self.create_transaction(price=1.5,stop=1.5050,risk=-0.01)
        position = Position(transaction.trade_details, 10000, spread=2)
        self.assertEquals(transaction.pnl, position.pnl_history[-1])

    def test_revalue_position_should_return_0_pnl_if_no_close_out(self):
        transaction = self.create_transaction(price=1.5,stop=1.5050,risk=-0.01)
        position = Position(transaction.trade_details, 10000)
        instruction = self.create_trade_line(price=1.4990,stop=1.5050,risk=0)
        candle = ohcl(instruction.price,instruction.price, instruction.price, instruction.price)
        position.revalue_position(instruction, candle, 10000)
        self.assertEqual(0, position.pnl_history[-1])

    def test_revalue_position_should_close_stop_outs_at_loss(self):
        transaction = self.create_transaction(price=1.5,stop=1.5050,risk=-0.01)
        position = Position(transaction.trade_details, 10000)
        instruction = self.create_trade_line(price=1.5051,stop=1.5070,risk=0)
        candle = ohcl(instruction.price,instruction.price, instruction.price, instruction.price)
        position.revalue_position(instruction, candle, 10000)
        self.assertAlmostEqual(-100, position.pnl_history[-1])

    def test_revalue_position_should_close_stop_outs_are_triggered_at_spread_minus_stop_for_shorts(self):
        transaction = self.create_transaction(price=1.5,stop=1.5050,risk=-0.01)
        position = Position(transaction.trade_details, 10000, spread=2.0)
        instruction = self.create_trade_line(price=1.5048,stop=1.5070,risk=0)
        candle = ohcl(instruction.price, c=1.5040, l= 1.5030, h=1.5048)
        position.revalue_position(instruction, candle, 10000)
        self.assertAlmostEqual(-104, position.pnl_history[-1])

    def test_revalue_position_should_close_stop_outs_are_triggered_at_spread_plus_stop_for_longs(self):
        transaction = self.create_transaction(price=1.5,stop=1.4950,risk=0.01)
        position = Position(transaction.trade_details, 10000, spread=2.0)
        instruction = self.create_trade_line(price=1.4980,stop=1.5070,risk=0)
        candle = ohcl(instruction.price, c=1.5040, l= 1.4948, h=1.5048)
        position.revalue_position(instruction, candle, 10000)
        self.assertAlmostEqual(-104, position.pnl_history[-1])

    def test_revalue_position_should_add_position_if_there_is_risk(self):
        transaction = self.create_transaction(price=1.5,stop=1.5050,risk=-0.01)
        position = Position(transaction.trade_details, 10000)
        instruction = self.create_trade_line(price=1.4990,stop=1.5040,risk=-0.01)
        candle = ohcl(instruction.price,instruction.price, instruction.price, instruction.price)
        position.revalue_position(instruction, candle, 10000)
        self.assertEqual(2, position.lines.__len__())

    def test_revalue_position_partial_close_out_should_not_change_amount_of_transactions(self):
        transaction = self.create_transaction(price=1.5,stop=1.5050,risk=-0.01)
        position = Position(transaction.trade_details, 10000)
        instruction = self.create_trade_line(price=1.4990,stop=1.4950,risk=0.005)
        candle = ohcl(instruction.price,instruction.price, instruction.price, instruction.price)
        position.revalue_position(instruction, candle, 10000)
        self.assertEqual(1, position.lines.__len__())

    def test_revalue_position_partial_close_out_should_set_residual_risk_correctly(self):
        transaction = self.create_transaction(price=1.5,stop=1.5050,risk=-0.01)
        position = Position(transaction.trade_details, 10000)
        instruction = self.create_trade_line(price=1.4990,stop=1.4950,risk=0.005)
        candle = ohcl(instruction.price,instruction.price, instruction.price, instruction.price)
        position.revalue_position(instruction, candle, 10000)
        self.assertAlmostEqual(-0.005, position.lines[0].risk)

    def test_revalue_position_full_close_out_should_capture_transaction_statistic_pnl(self):
        transaction = self.create_transaction(price=1.5,stop=1.5050,risk=-0.01)
        position = Position(transaction.trade_details, 10000)
        instruction = self.create_trade_line(price=1.4990,stop=1.4950,risk=0.01)
        candle = ohcl(instruction.price,instruction.price, instruction.price, instruction.price)
        position.revalue_position(instruction, candle, 10000)
        self.assertEqual(1, position.transaction_pnls.__len__())
        self.assertAlmostEqual(20, position.transaction_pnls[0].pnl)

    def test_revalue_position_stop_out_should_capture_transaction_statistic_pnl(self):
        transaction = self.create_transaction(price=1.5,stop=1.5050,risk=-0.01)
        position = Position(transaction.trade_details, 10000)
        instruction = self.create_trade_line(price=1.5050,stop=1.5025,risk=0.01)
        candle = ohcl(instruction.price,instruction.price, instruction.price, instruction.price)
        position.revalue_position(instruction, candle, 10000)
        self.assertEqual(1, position.transaction_pnls.__len__())
        self.assertAlmostEqual(-100, position.transaction_pnls[0].pnl)

    def test_revalue_position_partial_close_out_should_set_pnl_correctly(self):
        transaction = self.create_transaction(price=1.5,stop=1.5050,risk=-0.01)
        position = Position(transaction.trade_details, 10000)
        instruction = self.create_trade_line(price=1.4990,stop=1.4950,risk=0.005)
        candle = ohcl(instruction.price,instruction.price, instruction.price, instruction.price)
        position.revalue_position(instruction, candle, 10000)
        self.assertAlmostEqual(10, position.pnl_history[-1])

    def test_revalue_position_partial_close_out_should_set_pnl_correctly_on_multiple_legs(self):
        transaction = self.create_transaction(price=1.5, stop=1.5050, risk=-0.01)
        position = Position(transaction.trade_details, 10000)
        instruction1 = self.create_trade_line(price=1.4990, stop=1.4950, risk=0.005)
        candle1 = ohcl(instruction1.price,instruction1.price, instruction1.price, instruction1.price)
        position.revalue_position(instruction1, candle1, 10000)
        instruction2 = self.create_trade_line(price=1.4980, stop=1.4950, risk=0.005)
        candle2 = ohcl(instruction2.price,instruction2.price, instruction2.price, instruction2.price)
        position.revalue_position(instruction2, candle2, 10000)
        self.assertAlmostEqual(20, position.pnl_history[-1])
        self.assertAlmostEqual(30, sum(position.pnl_history))

    def test_revalue_position_partial_close_out_should_remove_transactions_correctly_on_multiple_legs(self):
        transaction = self.create_transaction(price=1.5, stop=1.5050, risk=-0.01)
        position = Position(transaction.trade_details, 10000)
        instruction = self.create_trade_line(price=1.4990, stop=1.4950, risk=0.005)
        candle = ohcl(instruction.price,instruction.price, instruction.price, instruction.price)
        position.revalue_position(instruction, candle, 10000)
        instruction = self.create_trade_line(price=1.4980, stop=1.4950, risk=0.005)
        candle = ohcl(instruction.price,instruction.price, instruction.price, instruction.price)
        position.revalue_position(instruction, candle, 10000)
        self.assertFalse(position.lines)

    def test_revalue_position_partial_close_out_should_set_correct_pnl_when_position_is_flipped(self):
        transaction = self.create_transaction(price=1.5, stop=1.5050, risk=-0.01)
        position = Position(transaction.trade_details, 10000)
        instruction1 = self.create_trade_line(price=1.4990, stop=1.4950, risk=0.005)
        candle1 = ohcl(instruction1.price,instruction1.price, instruction1.price, instruction1.price)
        position.revalue_position(instruction1, candle1, 10000)
        instruction2 = self.create_trade_line(price=1.4980, stop=1.4940, risk=0.01)
        candle2 = ohcl(instruction2.price,instruction2.price, instruction2.price, instruction2.price)
        position.revalue_position(instruction2, candle2, 10000)
        self.assertAlmostEqual(30, sum(position.pnl_history))

    def test_revalue_position_partial_close_out_should_set_correct_net_direction_when_position_is_flipped(self):
        transaction = self.create_transaction(price=1.5, stop=1.5050, risk=-0.01)
        position = Position(transaction.trade_details, 10000)
        instruction1 = self.create_trade_line(price=1.4990, stop=1.4950, risk=0.005)
        candle1 = ohcl(instruction1.price,instruction1.price, instruction1.price, instruction1.price)
        position.revalue_position(instruction1, candle1, 10000)
        instruction2 = self.create_trade_line(price=1.4980, stop=1.4940, risk=0.01)
        candle2 = ohcl(instruction2.price,instruction2.price, instruction2.price, instruction2.price)
        position.revalue_position(instruction2, candle2, 10000)
        self.assertEqual(Direction.Long, position.net_direction)

    def test_revalue_position_partial_close_out_should_set_correct_risk_direction_when_position_is_flipped(self):
        transaction = self.create_transaction(price=1.5, stop=1.5050, risk=-0.01)
        position = Position(transaction.trade_details, 10000)
        instruction1 = self.create_trade_line(price=1.4990, stop=1.4950, risk=0.005)
        candle1 = ohcl(instruction1.price,instruction1.price, instruction1.price, instruction1.price)
        position.revalue_position(instruction1, candle1, 10000)
        instruction2 = self.create_trade_line(price=1.4980, stop=1.4940, risk=0.01)
        candle2 = ohcl(instruction2.price,instruction2.price, instruction2.price, instruction2.price)
        position.revalue_position(instruction2, candle2, 10000)
        self.assertAlmostEqual(0.005, position.lines[0].risk)

    def test_revalue_position_stop_close_out_should_add_transaction_pnl(self):
        transaction = self.create_transaction(price=1.5,stop=1.5050,risk=-0.01)
        position = Position(transaction.trade_details, 10000)
        instruction1 = self.create_trade_line(price=1.5050,stop=1.4950,risk=0.01)
        candle1 = ohcl(instruction1.price,instruction1.price, instruction1.price, instruction1.price)
        position.revalue_position(instruction1, candle1, 10000)
        self.assertTrue(position.transaction_pnls[0])
        self.assertAlmostEqual(-100, position.transaction_pnls[0].pnl)

    def test_revalue_position_stop_using_candle_high_for_short(self):
        transaction = self.create_transaction(price=1.5,stop=1.5050,risk=-0.01)
        position = Position(transaction.trade_details, 10000)
        instruction1 = self.create_trade_line(price=1.5020,stop=1.4950,risk=0.01)
        candle1 = ohcl(instruction1.price,h=1.5050,l=instruction1.price,c=instruction1.price)
        position.revalue_position(instruction1, candle1, 10000)
        self.assertTrue(position.transaction_pnls[0])
        self.assertAlmostEqual(-100, position.transaction_pnls[0].pnl)

    def test_revalue_position_stop_using_candle_low_for_long(self):
        transaction = self.create_transaction(price=1.5,stop=1.4950,risk=0.01)
        position = Position(transaction.trade_details, 10000)
        instruction1 = self.create_trade_line(price=1.4990,stop=1.5000,risk=-0.01)
        candle1 = ohcl(instruction1.price,h=1.5050,l=1.4950,c=instruction1.price)
        position.revalue_position(instruction1, candle1, 10000)
        self.assertTrue(position.transaction_pnls[0])
        self.assertAlmostEqual(-100, position.transaction_pnls[0].pnl)

    def test_revalue_position_stop_out_should_not_stop_out_soft_stop_trade(self):
        transaction = self.create_transaction(price=1.5,stop=1.5050,risk=-0.01,stop_type=StopType.Soft)
        position = Position(transaction.trade_details, 10000)
        instruction = self.create_trade_line(price=1.5050,stop=1.5025,risk=0.0001)
        candle = ohcl(instruction.price,instruction.price, instruction.price, instruction.price)
        position.revalue_position(instruction, candle, 10000)
        self.assertEqual(0, len(position.transaction_pnls))

    def test_position_should_set_net_risk_correctly(self):
        transaction = self.create_transaction(currency="EURUSD")
        position = Position(transaction.trade_details, 10000)
        self.assertEqual(transaction.risk, position.net_risk)

    def test_get_net_risk_should_show_total_risk_correctly(self):
        transaction = self.create_transaction(price=1.5, stop=1.5050, risk=-0.01)
        position = Position(transaction.trade_details, 10000)
        instruction = self.create_trade_line(price=1.4990, stop=1.5050, risk=-0.005)
        candle = ohcl(instruction.price,instruction.price, instruction.price, instruction.price)
        position.revalue_position(instruction, candle, 10000)
        instruction = self.create_trade_line(price=1.4980, stop=1.5050, risk=-0.005)
        candle = ohcl(instruction.price,instruction.price, instruction.price, instruction.price)
        position.revalue_position(instruction, candle, 10000)
        self.assertAlmostEqual(-0.02, position.net_risk)





