"""In-memory implementation of CareSplitService.

Lets the whole app — UI, dashboard, reports — run with no database, no
network call, and no setup. Data lives only for the life of the process
(or the test) and is seeded with a starter set of categories on creation.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from caresplit_backend.domain import (
    Category,
    CategoryBreakdown,
    DashboardTotals,
    Expense,
    MonthBreakdown,
    Totals,
    YearlyReport,
)
from caresplit_backend.services.errors import CategoryInUseError, DuplicateCategoryError, NotFoundError

STARTER_CATEGORIES: list[tuple[str, Decimal]] = [
    ("Medical / doctor visits", Decimal("20")),
    ("Prescriptions", Decimal("20")),
    ("Medical equipment & supplies", Decimal("20")),
    ("In-home care / caregiving", Decimal("100")),
    ("Transportation", Decimal("100")),
    ("Other", Decimal("100")),
]


class MockCareSplitService:
    def __init__(self, seed: bool = True):
        self._categories: dict[int, Category] = {}
        self._expenses: dict[int, Expense] = {}
        self._next_category_id = 1
        self._next_expense_id = 1
        if seed:
            for name, pct_me in STARTER_CATEGORIES:
                self.create_category(name, pct_me)

    # -- categories ---------------------------------------------------

    def list_categories(self) -> list[Category]:
        return sorted(self._categories.values(), key=lambda c: c.name.lower())

    def get_category(self, category_id: int) -> Category:
        try:
            return self._categories[category_id]
        except KeyError:
            raise NotFoundError("Category", category_id) from None

    def create_category(self, name: str, pct_me: Decimal, notes: str = "") -> Category:
        name = name.strip()
        if any(c.name.lower() == name.lower() for c in self._categories.values()):
            raise DuplicateCategoryError(name)
        category = Category(id=self._next_category_id, name=name, pct_me=pct_me, notes=notes)
        self._categories[category.id] = category
        self._next_category_id += 1
        return category

    def update_category(
        self,
        category_id: int,
        *,
        name: Optional[str] = None,
        pct_me: Optional[Decimal] = None,
        notes: Optional[str] = None,
    ) -> Category:
        category = self.get_category(category_id)
        if name is not None:
            new_name = name.strip()
            if any(
                c.id != category_id and c.name.lower() == new_name.lower()
                for c in self._categories.values()
            ):
                raise DuplicateCategoryError(new_name)
            category.name = new_name
        if pct_me is not None:
            category.pct_me = pct_me
        if notes is not None:
            category.notes = notes
        return category

    def delete_category(self, category_id: int) -> None:
        self.get_category(category_id)
        in_use = [e for e in self._expenses.values() if e.category_id == category_id]
        if in_use:
            raise CategoryInUseError(category_id, len(in_use))
        del self._categories[category_id]

    # -- expenses -------------------------------------------------------

    def list_expenses(self, category_id: Optional[int] = None) -> list[Expense]:
        expenses = self._expenses.values()
        if category_id is not None:
            expenses = (e for e in expenses if e.category_id == category_id)
        return sorted(expenses, key=lambda e: (e.date, e.id), reverse=True)

    def get_expense(self, expense_id: int) -> Expense:
        try:
            return self._expenses[expense_id]
        except KeyError:
            raise NotFoundError("Expense", expense_id) from None

    def create_expense(
        self,
        *,
        date: date,
        category_id: int,
        amount: Decimal,
        description: str = "",
        pct_me: Optional[Decimal] = None,
        note: str = "",
        receipt_filename: Optional[str] = None,
    ) -> Expense:
        category = self.get_category(category_id)
        expense = Expense(
            id=self._next_expense_id,
            date=date,
            category_id=category.id,
            category_name=category.name,
            amount=amount,
            pct_me=pct_me if pct_me is not None else category.pct_me,
            description=description.strip(),
            note=note.strip(),
            receipt_filename=receipt_filename,
        )
        self._expenses[expense.id] = expense
        self._next_expense_id += 1
        return expense

    def update_expense(
        self,
        expense_id: int,
        *,
        date: Optional[date] = None,
        category_id: Optional[int] = None,
        amount: Optional[Decimal] = None,
        description: Optional[str] = None,
        pct_me: Optional[Decimal] = None,
        note: Optional[str] = None,
        receipt_filename: Optional[str] = None,
    ) -> Expense:
        expense = self.get_expense(expense_id)
        if date is not None:
            expense.date = date
        if category_id is not None:
            category = self.get_category(category_id)
            expense.category_id = category.id
            expense.category_name = category.name
        if amount is not None:
            expense.amount = amount
        if pct_me is not None:
            expense.pct_me = pct_me
        if description is not None:
            expense.description = description.strip()
        if note is not None:
            expense.note = note.strip()
        if receipt_filename is not None:
            expense.receipt_filename = receipt_filename
        return expense

    def delete_expense(self, expense_id: int) -> None:
        self.get_expense(expense_id)
        del self._expenses[expense_id]

    # -- aggregates -------------------------------------------------------

    def dashboard_totals(self, today: date) -> DashboardTotals:
        year_expenses = [e for e in self._expenses.values() if e.date.year == today.year]
        month_expenses = [e for e in year_expenses if e.date.month == today.month]
        recent = sorted(
            self._expenses.values(), key=lambda e: (e.date, e.id), reverse=True
        )[:8]
        return DashboardTotals(
            month=Totals.of(month_expenses),
            year=Totals.of(year_expenses),
            recent=recent,
        )

    def available_years(self) -> list[int]:
        years = {e.date.year for e in self._expenses.values()}
        return sorted(years, reverse=True)

    def yearly_report(self, year: int) -> YearlyReport:
        year_expenses = [e for e in self._expenses.values() if e.date.year == year]

        by_category_map: dict[str, list[Expense]] = {}
        for e in year_expenses:
            by_category_map.setdefault(e.category_name, []).append(e)
        by_category = [
            CategoryBreakdown(category_name=name, totals=Totals.of(items))
            for name, items in sorted(
                by_category_map.items(), key=lambda kv: Totals.of(kv[1]).total, reverse=True
            )
        ]

        by_month = []
        for month in range(1, 13):
            month_items = [e for e in year_expenses if e.date.month == month]
            if month_items:
                by_month.append(MonthBreakdown(month=month, totals=Totals.of(month_items)))

        return YearlyReport(
            year=year,
            totals=Totals.of(year_expenses),
            by_category=by_category,
            by_month=by_month,
        )
