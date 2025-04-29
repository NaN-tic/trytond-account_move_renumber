import unittest
from decimal import Decimal

from proteus import Model, Wizard
from trytond.modules.account.tests.tools import (create_chart,
                                                 create_fiscalyear,
                                                 get_accounts)
from trytond.modules.company.tests.tools import create_company, get_company
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules


class Test(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):

        # Install account_move_renumber
        activate_modules('account_move_renumber')

        # Create company
        _ = create_company()
        company = get_company()

        # Create fiscal year
        fiscalyear = create_fiscalyear(company)
        fiscalyear.click('create_period')
        period = fiscalyear.periods[0]

        # Create chart of accounts
        _ = create_chart(company)
        accounts = get_accounts(company)
        receivable = accounts['receivable']
        cash = accounts['cash']

        # Create parties
        Party = Model.get('party.party')
        customer = Party(name='Customer')
        customer.save()

        # Create and post Moves in Cash Journal
        Journal = Model.get('account.journal')
        Move = Model.get('account.move')
        journal_cash, = Journal.find([
            ('code', '=', 'CASH'),
        ])
        moves = []
        for i in range(10):
            move = Move()
            move.period = period
            move.journal = journal_cash
            move.date = period.start_date if i % 2 else period.end_date
            line = move.lines.new()
            line.account = cash
            line.debit = Decimal(42 + i)
            line = move.lines.new()
            line.account = receivable
            line.credit = Decimal(42 + i)
            line.party = customer
            moves.append(move)
        Move.click(moves, 'post')

        # Check post numbers
        moves = Move.find([], order=[('id', 'ASC')])
        self.assertEqual(len(moves), 10)
        self.assertEqual(
            all(move.number == str(i + 1) for i, move in enumerate(moves)),
            True)
        moves = Move.find([], order=[('date', 'ASC'), ('id', 'ASC')])
        self.assertEqual(
            all(move.number == str(i + 1) for i, move in enumerate(moves)),
            False)

        # Renumber moves
        renumber_moves = Wizard('account.move.renumber')
        renumber_moves.form.fiscalyear = fiscalyear
        renumber_moves.form.first_number = 1
        renumber_moves.execute('renumber')

        # Check post numbers after renumbering
        moves = Move.find([], order=[('date', 'ASC'), ('id', 'ASC')])
        self.assertEqual(len(moves), 10)
        self.assertEqual(
            all(move.number == str(i + 1) for i, move in enumerate(moves)),
            True)
        self.assertEqual(moves[-1].number, '10')
