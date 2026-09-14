from datetime import date
from decimal import Decimal

from caresplit_backend.domain import Category, Expense, Totals


def test_category_pct_insurance_is_the_complement():
    category = Category(id=1, name="Medical", pct_me=Decimal("20"))
    assert category.pct_insurance == Decimal("80")


def test_expense_split_amounts():
    expense = Expense(
        id=1,
        date=date(2026, 1, 1),
        category_id=1,
        category_name="Medical",
        amount=Decimal("100.00"),
        pct_me=Decimal("20"),
    )
    assert expense.amount_me == Decimal("20.00")
    assert expense.amount_insurance == Decimal("80.00")
    assert expense.amount_me + expense.amount_insurance == expense.amount


def test_expense_split_rounds_to_the_cent():
    # 33.33% of $10.00 is $3.333 -> rounds to $3.33, remainder $6.67
    expense = Expense(
        id=1,
        date=date(2026, 1, 1),
        category_id=1,
        category_name="Medical",
        amount=Decimal("10.00"),
        pct_me=Decimal("33.33"),
    )
    assert expense.amount_me == Decimal("3.33")
    assert expense.amount_insurance == Decimal("6.67")
    assert expense.amount_me + expense.amount_insurance == expense.amount


def test_totals_of_empty_list():
    totals = Totals.of([])
    assert totals.total == Decimal("0.00")
    assert totals.me == Decimal("0.00")
    assert totals.insurance == Decimal("0.00")


def test_totals_of_sums_correctly():
    expenses = [
        Expense(
            id=1,
            date=date(2026, 1, 1),
            category_id=1,
            category_name="Medical",
            amount=Decimal("100.00"),
            pct_me=Decimal("20"),
        ),
        Expense(
            id=2,
            date=date(2026, 1, 2),
            category_id=2,
            category_name="Transportation",
            amount=Decimal("50.00"),
            pct_me=Decimal("100"),
        ),
    ]
    totals = Totals.of(expenses)
    assert totals.total == Decimal("150.00")
    assert totals.me == Decimal("70.00")
    assert totals.insurance == Decimal("80.00")
