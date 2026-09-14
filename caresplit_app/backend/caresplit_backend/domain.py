"""Plain data types shared by every service implementation and the UI.

Framework-free on purpose: nothing here should import NiceGUI, a database
driver, or an HTTP client, so it can be reused unchanged by a mock service,
a real service, and their tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

TWO_PLACES = Decimal("0.01")


def _money(value) -> Decimal:
    return Decimal(str(value)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


@dataclass
class Category:
    id: int
    name: str
    pct_me: Decimal
    notes: str = ""

    @property
    def pct_insurance(self) -> Decimal:
        return Decimal("100") - self.pct_me


@dataclass
class Expense:
    id: int
    date: date
    category_id: int
    category_name: str
    amount: Decimal
    pct_me: Decimal
    description: str = ""
    note: str = ""
    receipt_filename: str | None = None

    @property
    def pct_insurance(self) -> Decimal:
        return Decimal("100") - self.pct_me

    @property
    def amount_me(self) -> Decimal:
        return _money(self.amount * self.pct_me / Decimal("100"))

    @property
    def amount_insurance(self) -> Decimal:
        return _money(self.amount) - self.amount_me


@dataclass
class Totals:
    """Total / my-share / insurance-share, used by the dashboard and reports."""

    total: Decimal = field(default_factory=lambda: Decimal("0.00"))
    me: Decimal = field(default_factory=lambda: Decimal("0.00"))
    insurance: Decimal = field(default_factory=lambda: Decimal("0.00"))

    @classmethod
    def of(cls, expenses: list[Expense]) -> "Totals":
        total = sum((_money(e.amount) for e in expenses), Decimal("0.00"))
        me = sum((e.amount_me for e in expenses), Decimal("0.00"))
        return cls(total=total, me=me, insurance=total - me)


@dataclass
class DashboardTotals:
    month: Totals
    year: Totals
    recent: list[Expense]


@dataclass
class MonthBreakdown:
    month: int
    totals: Totals


@dataclass
class CategoryBreakdown:
    category_name: str
    totals: Totals


@dataclass
class YearlyReport:
    year: int
    totals: Totals
    by_category: list[CategoryBreakdown]
    by_month: list[MonthBreakdown]
