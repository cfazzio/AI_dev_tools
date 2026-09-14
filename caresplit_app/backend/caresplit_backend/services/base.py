"""The service contract. Every backend call the UI makes goes through this.

Anything implementing this Protocol — the in-process mock, the HTTP-backed
ApiCareSplitService — is a drop-in replacement for the UI. No UI module
should import a concrete service class directly; always go through
:func:`caresplit_frontend.services.get_service`.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional, Protocol

from caresplit_backend.domain import Category, DashboardTotals, Expense, YearlyReport


class CareSplitService(Protocol):
    # -- categories ---------------------------------------------------
    def list_categories(self) -> list[Category]: ...

    def get_category(self, category_id: int) -> Category: ...

    def create_category(
        self, name: str, pct_me: Decimal, notes: str = ""
    ) -> Category: ...

    def update_category(
        self,
        category_id: int,
        *,
        name: Optional[str] = None,
        pct_me: Optional[Decimal] = None,
        notes: Optional[str] = None,
    ) -> Category: ...

    def delete_category(self, category_id: int) -> None: ...

    # -- expenses -------------------------------------------------------
    def list_expenses(self, category_id: Optional[int] = None) -> list[Expense]: ...

    def get_expense(self, expense_id: int) -> Expense: ...

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
    ) -> Expense: ...

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
    ) -> Expense: ...

    def delete_expense(self, expense_id: int) -> None: ...

    # -- aggregates -------------------------------------------------------
    def dashboard_totals(self, today: date) -> DashboardTotals: ...

    def available_years(self) -> list[int]: ...

    def yearly_report(self, year: int) -> YearlyReport: ...
