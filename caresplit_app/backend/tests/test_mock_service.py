from datetime import date
from decimal import Decimal

import pytest

from caresplit_backend.services.errors import (
    CategoryInUseError,
    DuplicateCategoryError,
    NotFoundError,
)
from caresplit_backend.services.mock_service import STARTER_CATEGORIES, MockCareSplitService


def test_new_service_is_seeded_with_starter_categories():
    service = MockCareSplitService()
    names = {c.name for c in service.list_categories()}
    assert names == {name for name, _ in STARTER_CATEGORIES}


def test_unseeded_service_starts_empty():
    service = MockCareSplitService(seed=False)
    assert service.list_categories() == []


# -- categories -----------------------------------------------------------


def test_create_and_get_category():
    service = MockCareSplitService(seed=False)
    category = service.create_category("Dental", Decimal("50"))
    assert service.get_category(category.id) == category
    assert category.pct_insurance == Decimal("50")


def test_create_category_rejects_duplicate_name_case_insensitive():
    service = MockCareSplitService(seed=False)
    service.create_category("Dental", Decimal("50"))
    with pytest.raises(DuplicateCategoryError):
        service.create_category("dental", Decimal("10"))


def test_get_missing_category_raises_not_found():
    service = MockCareSplitService(seed=False)
    with pytest.raises(NotFoundError):
        service.get_category(999)


def test_update_category_changes_split():
    service = MockCareSplitService(seed=False)
    category = service.create_category("Dental", Decimal("50"))
    updated = service.update_category(category.id, pct_me=Decimal("75"))
    assert updated.pct_me == Decimal("75")
    assert updated.pct_insurance == Decimal("25")


def test_delete_unused_category_succeeds():
    service = MockCareSplitService(seed=False)
    category = service.create_category("Dental", Decimal("50"))
    service.delete_category(category.id)
    with pytest.raises(NotFoundError):
        service.get_category(category.id)


def test_delete_category_in_use_is_blocked():
    service = MockCareSplitService(seed=False)
    category = service.create_category("Dental", Decimal("50"))
    service.create_expense(date=date(2026, 1, 1), category_id=category.id, amount=Decimal("10"))
    with pytest.raises(CategoryInUseError):
        service.delete_category(category.id)
    # still there afterward
    assert service.get_category(category.id) is not None


# -- expenses ---------------------------------------------------------------


def test_create_expense_inherits_category_split_by_default():
    service = MockCareSplitService(seed=False)
    category = service.create_category("Medical", Decimal("20"))
    expense = service.create_expense(
        date=date(2026, 1, 1), category_id=category.id, amount=Decimal("100.00")
    )
    assert expense.pct_me == Decimal("20")
    assert expense.amount_me == Decimal("20.00")


def test_create_expense_can_override_split():
    service = MockCareSplitService(seed=False)
    category = service.create_category("Medical", Decimal("20"))
    expense = service.create_expense(
        date=date(2026, 1, 1),
        category_id=category.id,
        amount=Decimal("100.00"),
        pct_me=Decimal("100"),
    )
    assert expense.pct_me == Decimal("100")
    assert expense.amount_me == Decimal("100.00")
    # category default is untouched
    assert service.get_category(category.id).pct_me == Decimal("20")


def test_create_expense_for_missing_category_raises_not_found():
    service = MockCareSplitService(seed=False)
    with pytest.raises(NotFoundError):
        service.create_expense(date=date(2026, 1, 1), category_id=999, amount=Decimal("10"))


def test_update_expense_recalculates_split_when_category_changes():
    service = MockCareSplitService(seed=False)
    medical = service.create_category("Medical", Decimal("20"))
    transport = service.create_category("Transportation", Decimal("100"))
    expense = service.create_expense(
        date=date(2026, 1, 1), category_id=medical.id, amount=Decimal("10")
    )
    assert expense.category_name == "Medical"

    updated = service.update_expense(expense.id, category_id=transport.id)
    assert updated.category_name == "Transportation"
    # pct_me is left as-is on update unless explicitly passed
    assert updated.pct_me == Decimal("20")


def test_delete_expense():
    service = MockCareSplitService(seed=False)
    category = service.create_category("Medical", Decimal("20"))
    expense = service.create_expense(
        date=date(2026, 1, 1), category_id=category.id, amount=Decimal("10")
    )
    service.delete_expense(expense.id)
    with pytest.raises(NotFoundError):
        service.get_expense(expense.id)


def test_list_expenses_filters_by_category():
    service = MockCareSplitService(seed=False)
    medical = service.create_category("Medical", Decimal("20"))
    transport = service.create_category("Transportation", Decimal("100"))
    service.create_expense(date=date(2026, 1, 1), category_id=medical.id, amount=Decimal("10"))
    service.create_expense(date=date(2026, 1, 2), category_id=transport.id, amount=Decimal("20"))

    assert len(service.list_expenses()) == 2
    assert len(service.list_expenses(category_id=medical.id)) == 1
    assert service.list_expenses(category_id=medical.id)[0].category_name == "Medical"


def test_list_expenses_orders_newest_first():
    service = MockCareSplitService(seed=False)
    category = service.create_category("Medical", Decimal("20"))
    older = service.create_expense(
        date=date(2026, 1, 1), category_id=category.id, amount=Decimal("10")
    )
    newer = service.create_expense(
        date=date(2026, 2, 1), category_id=category.id, amount=Decimal("20")
    )
    assert [e.id for e in service.list_expenses()] == [newer.id, older.id]


# -- aggregates -------------------------------------------------------------


def test_dashboard_totals_split_month_and_year():
    service = MockCareSplitService(seed=False)
    category = service.create_category("Medical", Decimal("20"))
    # this month
    service.create_expense(
        date=date(2026, 3, 15), category_id=category.id, amount=Decimal("100.00")
    )
    # same year, different month
    service.create_expense(
        date=date(2026, 1, 1), category_id=category.id, amount=Decimal("50.00")
    )
    # different year entirely
    service.create_expense(
        date=date(2025, 3, 15), category_id=category.id, amount=Decimal("999.00")
    )

    totals = service.dashboard_totals(today=date(2026, 3, 20))
    assert totals.month.total == Decimal("100.00")
    assert totals.month.me == Decimal("20.00")
    assert totals.year.total == Decimal("150.00")
    assert totals.year.me == Decimal("30.00")


def test_available_years_and_yearly_report():
    service = MockCareSplitService(seed=False)
    medical = service.create_category("Medical", Decimal("20"))
    transport = service.create_category("Transportation", Decimal("100"))
    service.create_expense(date=date(2026, 1, 5), category_id=medical.id, amount=Decimal("100"))
    service.create_expense(date=date(2026, 2, 5), category_id=transport.id, amount=Decimal("50"))
    service.create_expense(date=date(2025, 6, 1), category_id=medical.id, amount=Decimal("10"))

    assert service.available_years() == [2026, 2025]

    report = service.yearly_report(2026)
    assert report.totals.total == Decimal("150.00")
    assert report.totals.me == Decimal("20.00") + Decimal("50.00")

    by_category = {row.category_name: row.totals for row in report.by_category}
    assert by_category["Medical"].total == Decimal("100.00")
    assert by_category["Transportation"].total == Decimal("50.00")

    months = {row.month for row in report.by_month}
    assert months == {1, 2}


def test_yearly_report_for_year_with_no_expenses_is_empty():
    service = MockCareSplitService(seed=False)
    report = service.yearly_report(2030)
    assert report.totals.total == Decimal("0.00")
    assert report.by_category == []
    assert report.by_month == []
