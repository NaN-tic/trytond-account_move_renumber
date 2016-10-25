==============================
Account Move Renumber Scenario
==============================

=============
General Setup
=============

Imports::

    >>> from decimal import Decimal
    >>> from proteus import Model, Wizard
    >>> from trytond.tests.tools import activate_modules
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> from trytond.modules.account.tests.tools import create_fiscalyear, \
    ...     create_chart, get_accounts, create_tax, set_tax_code

Install account_move_renumber::

    >>> config = activate_modules('account_move_renumber')

Create company::

    >>> _ = create_company()
    >>> company = get_company()

Create fiscal year::

    >>> fiscalyear = create_fiscalyear(company)
    >>> fiscalyear.click('create_period')
    >>> period = fiscalyear.periods[0]

Create chart of accounts::

    >>> _ = create_chart(company)
    >>> accounts = get_accounts(company)
    >>> receivable = accounts['receivable']
    >>> revenue = accounts['revenue']
    >>> expense = accounts['expense']
    >>> cash = accounts['cash']

Create parties::

    >>> Party = Model.get('party.party')
    >>> customer = Party(name='Customer')
    >>> customer.save()

Create and post Moves in Cash Journal::

    >>> Journal = Model.get('account.journal')
    >>> Move = Model.get('account.move')
    >>> journal_cash, = Journal.find([
    ...         ('code', '=', 'CASH'),
    ...         ])
    >>> moves = []
    >>> for i in range(10):
    ...     move = Move()
    ...     move.period = period
    ...     move.journal = journal_cash
    ...     move.date = period.start_date if i% 2 else period.end_date
    ...     line = move.lines.new()
    ...     line.account = cash
    ...     line.debit = Decimal(42 + i)
    ...     line = move.lines.new()
    ...     line.account = receivable
    ...     line.credit = Decimal(42 + i)
    ...     line.party = customer
    ...     moves.append(move)
    >>> Move.click(moves, 'post')

Check post numbers::

    >>> moves = Move.find([], order=[('id', 'ASC')])
    >>> len(moves)
    10
    >>> all(move.post_number == str(i + 1) for i, move in enumerate(moves))
    True
    >>> moves = Move.find([], order=[('date', 'ASC'), ('id', 'ASC')])
    >>> all(move.post_number == str(i + 1) for i, move in enumerate(moves))
    False

Renumber moves::

    >>> renumber_moves = Wizard('account.move.renumber')
    >>> renumber_moves.form.fiscalyear = fiscalyear
    >>> renumber_moves.form.first_number = 1
    >>> renumber_moves.execute('renumber')

Check post numbers after renumbering::

    >>> moves = Move.find([], order=[('date', 'ASC'), ('id', 'ASC')])
    >>> len(moves)
    10
    >>> all(move.post_number == str(i + 1) for i, move in enumerate(moves))
    True
    >>> moves[-1].post_number
    u'10'
