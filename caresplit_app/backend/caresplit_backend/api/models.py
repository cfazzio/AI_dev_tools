"""Pydantic request/response schemas matching openapi.yaml's components.schemas.

Field names are snake_case in Python, camelCase on the wire (matching the
spec) via `alias_generator`. Money and percentages are plain `str` fields,
not `Decimal` or `float` — the spec serializes them as decimal strings to
avoid float round-tripping, and the `*_to_response` converters below are
the one place that turns a domain `Decimal` into that string.
"""

from __future__ import annotations

from datetime import date as date_type
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from caresplit_backend.domain import (
    Category as DomainCategory,
    DashboardTotals as DomainDashboardTotals,
    Expense as DomainExpense,
    Totals as DomainTotals,
    YearlyReport as DomainYearlyReport,
)


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


# -- categories -------------------------------------------------------


class Category(CamelModel):
    id: int
    name: str
    pct_me: str
    pct_insurance: str
    notes: str


class CategoryCreate(CamelModel):
    name: str
    pct_me: str
    notes: str = ""


class CategoryUpdate(CamelModel):
    name: str | None = None
    pct_me: str | None = None
    notes: str | None = None


def category_to_response(c: DomainCategory) -> Category:
    return Category(
        id=c.id,
        name=c.name,
        pct_me=str(c.pct_me),
        pct_insurance=str(c.pct_insurance),
        notes=c.notes,
    )


# -- expenses -------------------------------------------------------


class Expense(CamelModel):
    id: int
    date: date_type
    category_id: int
    category_name: str
    amount: str
    pct_me: str
    pct_insurance: str
    amount_me: str
    amount_insurance: str
    description: str
    note: str
    receipt_filename: str | None


class ExpenseCreate(CamelModel):
    date: date_type
    category_id: int
    amount: str
    description: str = ""
    pct_me: str | None = None
    note: str = ""
    receipt_filename: str | None = None


class ExpenseUpdate(CamelModel):
    date: Optional[date_type] = None
    category_id: int | None = None
    amount: str | None = None
    description: str | None = None
    pct_me: str | None = None
    note: str | None = None
    receipt_filename: str | None = None


def expense_to_response(e: DomainExpense) -> Expense:
    return Expense(
        id=e.id,
        date=e.date,
        category_id=e.category_id,
        category_name=e.category_name,
        amount=str(e.amount),
        pct_me=str(e.pct_me),
        pct_insurance=str(e.pct_insurance),
        amount_me=str(e.amount_me),
        amount_insurance=str(e.amount_insurance),
        description=e.description,
        note=e.note,
        receipt_filename=e.receipt_filename,
    )


# -- aggregates -------------------------------------------------------


class Totals(CamelModel):
    total: str
    me: str
    insurance: str


def totals_to_response(t: DomainTotals) -> Totals:
    return Totals(total=str(t.total), me=str(t.me), insurance=str(t.insurance))


class DashboardTotals(CamelModel):
    month: Totals
    year: Totals
    recent: list[Expense]


def dashboard_to_response(d: DomainDashboardTotals) -> DashboardTotals:
    return DashboardTotals(
        month=totals_to_response(d.month),
        year=totals_to_response(d.year),
        recent=[expense_to_response(e) for e in d.recent],
    )


class CategoryBreakdown(CamelModel):
    category_name: str
    totals: Totals


class MonthBreakdown(CamelModel):
    month: int
    totals: Totals


class YearlyReport(CamelModel):
    year: int
    totals: Totals
    by_category: list[CategoryBreakdown]
    by_month: list[MonthBreakdown]


def yearly_report_to_response(r: DomainYearlyReport) -> YearlyReport:
    return YearlyReport(
        year=r.year,
        totals=totals_to_response(r.totals),
        by_category=[
            CategoryBreakdown(category_name=row.category_name, totals=totals_to_response(row.totals))
            for row in r.by_category
        ],
        by_month=[
            MonthBreakdown(month=row.month, totals=totals_to_response(row.totals))
            for row in r.by_month
        ],
    )


# -- auth -------------------------------------------------------


class LoginRequest(CamelModel):
    username: str
    password: str


class TokenResponse(CamelModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


# -- errors -------------------------------------------------------


class Error(CamelModel):
    message: str
